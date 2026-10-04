"""Búsqueda y ficha puntual de abogados inscritos en el Foro."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from itertools import islice, permutations
import re
from threading import Lock, Thread
import time
import unicodedata
from typing import Annotated

from bs4 import BeautifulSoup
import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, sessionmaker

from govdata.application.dto.identificacion_cedula_dto import EstadoMatchingCedula
from govdata.application.services.consulta_cedula_cascada import consultar_cedula_en_cascada
from govdata.domain.exceptions.domain_exceptions import FuenteCedulaNoDisponibleError
from govdata.domain.rules.matching_cedula import hacer_matching_cedula
from govdata.domain.rules.matching_cedula import normalizar_nombre
from govdata.infrastructure.scraping.playwright.foro_abogados_adapter import (
    ForoAbogadosPlaywrightAdapter,
    FuenteForoNoDisponibleError,
)
from govdata.infrastructure.scraping.playwright.fuentes_cedula import fuentes_consulta_cedula
from govdata.infrastructure.api.dependencies import get_sesion
from govdata.infrastructure.persistence.postgresql.models.abogado_ecuador_model import (
    AbogadoEcuadorModel,
)
from govdata.infrastructure.persistence.postgresql.models.directorio_profesional_derecho_model import (
    DirectorioProfesionalDerechoModel,
    EstadoDirectorioProfesionalesModel,
)
from govdata.config.settings import get_settings
from govdata.domain.rules.texto_humano import reparar_texto_humano

router = APIRouter(prefix="/abogados-ecuador", tags=["Abogados del Ecuador"])
_URL = "https://app.funcionjudicial.gob.ec/ForoAbogados/Publico/frmConsultasGenerales.jsp"
_carga_directorio_lock = Lock()
_REGISTROS_POR_PAGINA = 20
_PREFIJO_PROFESIONAL = re.compile(
    r"^\s*(?:(?:AB(?:G|OG(?:ADO|ADA)?)?|DR(?:A)?|LIC(?:ENCIADO|ADA)?)\.\s*|\.\s*)+",
    re.IGNORECASE,
)


def _limpiar_nombre_profesional(valor: str | None) -> str:
    """Quita tratamientos del directorio que no forman parte del nombre.

    El portal puede publicar ``.NOMBRE`` o ``AB. NOMBRE``. Esos textos no
    sirven como identificador de una persona y reducen la calidad de las
    consultas de coincidencia, por lo que se eliminan antes de mostrar,
    persistir o consultar fuentes externas.
    """
    limpio = _PREFIJO_PROFESIONAL.sub("", reparar_texto_humano(valor)).strip()
    return re.sub(r"(?:\s+null)+$", "", limpio, flags=re.IGNORECASE).strip()

def _normalizar(valor: str) -> str:
    sin_tildes = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", valor)
        if unicodedata.category(caracter) != "Mn"
    )
    return " ".join(re.sub(r"[^A-Za-z0-9 ]+", " ", sin_tildes.upper()).split())


def _variantes_busqueda(q: str) -> list[str]:
    """Genera órdenes humanos posibles sin convertir la consulta en un barrido.

    El Foro interpreta varios términos como una frase ordenada. Para hasta
    cuatro términos (el formato usual de nombres y apellidos) se prueban sus
    órdenes posibles, en lotes pequeños. Las entradas más largas conservan el
    orden escrito y su inverso para proteger a la fuente externa.
    """
    terminos = _normalizar(q).split()
    if len(terminos) <= 1:
        return [" ".join(terminos)]
    if len(terminos) > 4:
        return [" ".join(terminos), " ".join(reversed(terminos))]
    ordenes = list(dict.fromkeys(permutations(terminos)))
    # El Foro usa LIKE internamente. El comodín permite que los términos no
    # estén contiguos: “AYALA%DEXI” encuentra “AYALA SANTI DEXI VIRGINIA”.
    # Se mantienen también las frases para conservar el comportamiento de la
    # búsqueda nativa cuando los términos sí son consecutivos.
    return list(
        dict.fromkeys(
            [" ".join(orden) for orden in ordenes]
            + ["%".join(orden) for orden in ordenes]
        )
    )


def _parsear_resultados(html: str) -> list[dict[str, str]]:
    sopa = BeautifulSoup(html, "html.parser")
    resultados: list[dict[str, str]] = []
    for fila in sopa.select("tr[id^='Fila']"):
        celdas = [celda.get_text(" ", strip=True) for celda in fila.select("td")]
        if len(celdas) >= 7:
            resultados.append({"codigo": celdas[-7], "matricula": celdas[-6], "nombre_completo": _limpiar_nombre_profesional(celdas[-5]), "direccion_oficina": celdas[-4], "inscripcion": celdas[-3], "credencial": celdas[-2], "estado": celdas[-1]})
    return resultados


def _total_registros(html: str) -> int | None:
    coincidencia = re.search(r"([0-9.]+)\s+Registros\s+en\s+total", html, re.IGNORECASE)
    return int(coincidencia.group(1).replace(".", "")) if coincidencia else None


def _estado_directorio(sesion: Session) -> EstadoDirectorioProfesionalesModel:
    estado = sesion.get(EstadoDirectorioProfesionalesModel, 1)
    if estado is None:
        estado = EstadoDirectorioProfesionalesModel(id=1)
        sesion.add(estado)
        sesion.commit()
    return estado


def _cargar_pagina_directorio(pagina: int) -> tuple[list[dict[str, str]], int | None]:
    ultimo_error: Exception | None = None
    for intento in range(1, 5):
        try:
            respuesta = httpx.post(
                _URL,
                data={
                    "txtParametroBusqueda": "", "Operacion": "Buscar", "Op": "s0",
                    "txtNumeroPagina": str(pagina), "txtRegistrosPagina": str(_REGISTROS_POR_PAGINA),
                },
                timeout=45,
            )
            respuesta.raise_for_status()
            return _parsear_resultados(respuesta.text), _total_registros(respuesta.text)
        except (httpx.HTTPError, httpx.TransportError) as error:
            ultimo_error = error
            time.sleep(2 * intento)
    raise RuntimeError("La fuente externa no respondió después de varios reintentos") from ultimo_error


def _ejecutar_carga_directorio() -> None:
    """Carga pública, secuencial, reanudable y con una pausa amable al portal."""
    motor = create_engine(get_settings().database.dsn)
    fabrica_sesion = sessionmaker(bind=motor)
    try:
        with fabrica_sesion() as sesion:
            estado = _estado_directorio(sesion)
            pagina = max(estado.pagina_actual + 1, 1)
            estado.estado = "en_proceso"
            estado.mensaje = "En proceso, por favor espera."
            sesion.commit()
        while True:
            with fabrica_sesion() as sesion:
                estado = _estado_directorio(sesion)
                if estado.estado == "cancelando":
                    estado.estado = "pausado"
                    estado.mensaje = "Carga pausada. Puedes reanudarla cuando lo necesites."
                    sesion.commit()
                    return
            filas, total = _cargar_pagina_directorio(pagina)
            if not filas:
                with fabrica_sesion() as sesion:
                    estado = _estado_directorio(sesion)
                    estado.estado = "completado"
                    estado.mensaje = "Directorio de profesionales actualizado correctamente."
                    sesion.commit()
                return
            ahora = datetime.now(UTC)
            lote = [{
                "codigo_foro": int(fila["codigo"]), "matricula": reparar_texto_humano(fila["matricula"]),
                "nombre_completo": _limpiar_nombre_profesional(fila["nombre_completo"]),
                "direccion_oficina": reparar_texto_humano(fila["direccion_oficina"]),
                "inscripcion": reparar_texto_humano(fila["inscripcion"]),
                "credencial": reparar_texto_humano(fila["credencial"]), "estado": reparar_texto_humano(fila["estado"]),
                "cargado_en": ahora,
            } for fila in filas if fila.get("codigo", "").isdigit()]
            if lote:
                with fabrica_sesion() as sesion:
                    sentencia = insert(DirectorioProfesionalDerechoModel).values(lote)
                    actualizables = {campo: getattr(sentencia.excluded, campo) for campo in lote[0] if campo != "codigo_foro"}
                    sesion.execute(sentencia.on_conflict_do_update(index_elements=["codigo_foro"], set_=actualizables))
                    estado = _estado_directorio(sesion)
                    estado.total_esperado = total or estado.total_esperado
                    estado.pagina_actual = pagina
                    estado.registros_guardados = sesion.scalar(select(func.count()).select_from(DirectorioProfesionalDerechoModel)) or 0
                    estado.estado = "en_proceso"
                    estado.mensaje = "En proceso, por favor espera."
                    sesion.commit()
            pagina += 1
            # No se consulta detalle y se mantiene una cadencia moderada.
            time.sleep(0.4)
    except Exception as error:
        with fabrica_sesion() as sesion:
            estado = _estado_directorio(sesion)
            estado.estado = "error"
            estado.mensaje = "La carga se pausó porque la fuente externa no respondió. Puedes intentar nuevamente."
            sesion.commit()
    finally:
        motor.dispose()
        _carga_directorio_lock.release()


async def _buscar_variante(cliente: httpx.AsyncClient, variante: str) -> list[dict[str, str]]:
    respuesta = await cliente.post(
        _URL,
        data={"txtParametroBusqueda": variante, "Operacion": "Buscar", "Op": "s0", "txtNumeroPagina": "1", "txtRegistrosPagina": "20"},
    )
    respuesta.raise_for_status()
    return _parsear_resultados(respuesta.text)


def _coinciden_todos_los_terminos(item: dict[str, str], terminos: set[str]) -> bool:
    nombre = set(_normalizar(item["nombre_completo"]).split())
    return terminos.issubset(nombre)


@router.get("/directorio/estado")
def estado_directorio_profesionales(sesion: Annotated[Session, Depends(get_sesion)]) -> dict:
    estado = _estado_directorio(sesion)
    total = sesion.scalar(select(func.count()).select_from(DirectorioProfesionalDerechoModel)) or 0
    return {
        "estado": estado.estado, "mensaje": estado.mensaje, "total_esperado": estado.total_esperado,
        "pagina_actual": estado.pagina_actual, "registros_guardados": total,
        "actualizado_en": estado.actualizado_en,
    }


@router.post("/directorio/actualizar", status_code=202)
def actualizar_directorio_profesionales(sesion: Annotated[Session, Depends(get_sesion)]) -> dict:
    if not _carga_directorio_lock.acquire(blocking=False):
        return {"iniciado": False, "mensaje": "Ya hay una carga en proceso."}
    estado = _estado_directorio(sesion)
    # Una carga terminada inicia una revisión completa; una pausada reanuda
    # desde la última página persistida.
    # Un error temporal conserva la última página confirmada: reintentar
    # debe continuar desde allí, nunca volver a recorrer miles de páginas.
    if estado.estado in {"completado", "inactivo"}:
        estado.pagina_actual = 0
    estado.estado = "en_proceso"
    estado.mensaje = "En proceso, por favor espera."
    sesion.commit()
    Thread(target=_ejecutar_carga_directorio, name="carga-directorio-profesionales", daemon=True).start()
    return {"iniciado": True, "mensaje": "En proceso, por favor espera."}


@router.post("/directorio/cancelar")
def cancelar_directorio_profesionales(sesion: Annotated[Session, Depends(get_sesion)]) -> dict:
    estado = _estado_directorio(sesion)
    if estado.estado == "en_proceso":
        estado.estado = "cancelando"
        estado.mensaje = "Pausando la carga…"
        sesion.commit()
    return {"mensaje": estado.mensaje, "estado": estado.estado}


@router.get("/directorio")
def listar_directorio_profesionales(
    q: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
    sesion: Session = Depends(get_sesion),
) -> dict:
    consulta = select(DirectorioProfesionalDerechoModel)
    if q:
        for termino in _normalizar(q).split():
            consulta = consulta.where(DirectorioProfesionalDerechoModel.nombre_completo.ilike(f"%{termino}%"))
    total = sesion.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    items = sesion.scalars(
        consulta.order_by(DirectorioProfesionalDerechoModel.nombre_completo)
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"items": [{
        "codigo": str(item.codigo_foro), "matricula": item.matricula, "nombre_completo": _limpiar_nombre_profesional(item.nombre_completo),
        "direccion_oficina": item.direccion_oficina, "inscripcion": item.inscripcion,
        "credencial": item.credencial, "estado": item.estado,
    } for item in items], "total": total, "page": page, "page_size": page_size}


@router.get("/buscar")
async def buscar_abogados(q: str = Query(min_length=2, max_length=120)) -> dict:
    variantes = _variantes_busqueda(q)
    terminos = set(_normalizar(q).split())
    encontrados: dict[str, dict[str, str]] = {}
    # Tres peticiones como máximo a la vez: suficiente para una búsqueda
    # tolerante al orden sin ejecutar consultas masivas contra el Foro.
    async with httpx.AsyncClient(timeout=30) as cliente:
        iterador = iter(variantes)
        while lote := list(islice(iterador, 3)):
            respuestas = await asyncio.gather(
                *(_buscar_variante(cliente, variante) for variante in lote),
                return_exceptions=True,
            )
            for respuesta in respuestas:
                if isinstance(respuesta, Exception):
                    continue
                for item in respuesta:
                    encontrados[item["codigo"]] = item
            coincidencias = [
                item for item in encontrados.values()
                if _coinciden_todos_los_terminos(item, terminos)
            ]
            if coincidencias:
                return {"items": coincidencias, "total": len(coincidencias)}

    # Para una búsqueda de un solo término se conserva el listado del Foro;
    # con varios términos no se muestran personas que no contengan todos ellos.
    items = [
        item for item in encontrados.values()
        if len(terminos) == 1 or _coinciden_todos_los_terminos(item, terminos)
    ]
    return {"items": items, "total": len(items)}

def _detalle_publico(codigo: int) -> dict:
    respuesta = httpx.post("https://app.funcionjudicial.gob.ec/ForoAbogados/Publico/frmDetalleAbogado.jsp", data={"txtCodigo": str(codigo), "Operacion": "2"}, timeout=30)
    respuesta.raise_for_status()
    sopa = BeautifulSoup(respuesta.text, "html.parser")
    def valor(id_: str) -> str | None:
        nodo = sopa.find(id=id_)
        return nodo.get_text(" ", strip=True) if nodo else None
    return {"codigo": codigo, "nombre_completo": _limpiar_nombre_profesional(valor("NOMBRE")), "provincia": valor("descripcionProvincia"), "canton": valor("descripcionCanton"), "lugar_ejercicio": valor("descripcionProvinciaEP"), "lugar_inscripcion": valor("descripcionProvinciaInscripcion"), "fecha_inscripcion": valor("DTFECHA2"), "titulo": valor("DESCRIPCIONTITULO")}


def _datos_persistidos(ficha: AbogadoEcuadorModel) -> dict:
    return {
        "codigo": ficha.codigo_foro,
        "nombre_completo": ficha.nombre_completo,
        "ciudad": ficha.ciudad,
        "cedula": ficha.cedula,
        "correo": ficha.correo,
        "telefono_domicilio": ficha.telefono_domicilio,
        "direccion_domicilio": ficha.direccion_domicilio,
        "telefono_oficina": ficha.telefono_oficina,
        "direccion_oficina": ficha.direccion_oficina,
        "celular": ficha.celular,
    }


def _guardar_ficha(
    sesion: Session, codigo: int, nombre_completo: str | None, ciudad: str | None, cedula: str,
    correo: str | None, telefono_domicilio: str | None, direccion_domicilio: str | None,
    telefono_oficina: str | None, direccion_oficina: str | None, celular: str | None,
) -> None:
    ficha = sesion.scalar(select(AbogadoEcuadorModel).where(AbogadoEcuadorModel.codigo_foro == codigo))
    if ficha is None:
        ficha = AbogadoEcuadorModel(codigo_foro=codigo)
        sesion.add(ficha)
    ficha.nombre_completo = nombre_completo
    ficha.ciudad = ciudad
    ficha.cedula = cedula
    ficha.correo = correo
    ficha.telefono_domicilio = telefono_domicilio
    ficha.direccion_domicilio = direccion_domicilio
    ficha.telefono_oficina = telefono_oficina
    ficha.direccion_oficina = direccion_oficina
    ficha.celular = celular


@router.get("/consultados")
def listar_abogados_consultados(sesion: Annotated[Session, Depends(get_sesion)]) -> dict:
    """Historial local de fichas completas, sin volver a consultar fuentes."""
    fichas = sesion.scalars(
        select(AbogadoEcuadorModel).order_by(AbogadoEcuadorModel.actualizado_en.desc())
    ).all()
    return {"items": [{**_datos_persistidos(ficha), "estado_consulta": "completa"} for ficha in fichas], "total": len(fichas)}


def _separar_nombre(nombre_completo: str) -> tuple[str, str, str]:
    """El directorio público entrega los apellidos antes de los nombres."""
    partes = nombre_completo.split()
    if len(partes) >= 4:
        return " ".join(partes[2:]), partes[0], partes[1]
    if len(partes) == 3:
        return " ".join(partes[1:]), partes[0], ""
    return nombre_completo, "", ""


@router.get("/{codigo}/detalle")
def detalle_abogado(
    codigo: int, sesion: Annotated[Session, Depends(get_sesion)]
) -> dict:
    """Entrega el detalle público y los datos ya guardados de esa ficha."""
    publico = _detalle_publico(codigo)
    ficha = sesion.scalar(select(AbogadoEcuadorModel).where(AbogadoEcuadorModel.codigo_foro == codigo))
    if ficha is None:
        return publico
    return {**publico, **_datos_persistidos(ficha), "estado_consulta": "completa"}


@router.post("/{codigo}/consultar-detalles")
async def consultar_detalles_abogado(
    codigo: int, sesion: Annotated[Session, Depends(get_sesion)]
) -> dict:
    """Verifica en el Foro las identidades plausibles para la ficha elegida.

    Una única coincidencia verificada se persiste. Varias coincidencias se
    devuelven separadas; un error parcial impide declarar identidad única.
    """
    publico = _detalle_publico(codigo)
    nombre = publico.get("nombre_completo")
    if not nombre:
        return {**publico, "estado_consulta": "sin_nombre_publico"}

    nombres, apellido_paterno, apellido_materno = _separar_nombre(nombre)
    try:
        candidatos = await consultar_cedula_en_cascada(
            fuentes_consulta_cedula(), nombres, apellido_paterno, apellido_materno
        )
        coincidencia = hacer_matching_cedula(
            nombres, f"{apellido_paterno} {apellido_materno}".strip(), candidatos
        )
    except FuenteCedulaNoDisponibleError:
        return {**publico, "estado_consulta": "fuente_identificacion_no_disponible"}

    if coincidencia.estado not in {
        EstadoMatchingCedula.MATCH_EXACT,
        EstadoMatchingCedula.MATCH_HIGH_CONFIDENCE,
        EstadoMatchingCedula.AMBIGUOUS,
    }:
        return {**publico, "estado_consulta": coincidencia.estado.value}

    candidatos_verificar = ([coincidencia.candidato] if coincidencia.candidato else list(coincidencia.candidatos))
    candidatos_unicos = {c.cedula: c for c in candidatos_verificar}
    seleccionado = sesion.scalar(select(DirectorioProfesionalDerechoModel).where(DirectorioProfesionalDerechoModel.codigo_foro == codigo))
    matricula = seleccionado.matricula if seleccionado else None
    resultados = []
    fallos = 0
    for candidato in candidatos_unicos.values():
        try:
            registros = await ForoAbogadosPlaywrightAdapter().buscar_por_cedula(candidato.cedula)
        except FuenteForoNoDisponibleError:
            fallos += 1
            continue
        for registro in registros:
            if not registro.nombre_completo or sorted(normalizar_nombre(_limpiar_nombre_profesional(registro.nombre_completo)).split()) != sorted(normalizar_nombre(nombre).split()):
                continue
            if matricula and registro.registro and re.sub(r"\W", "", matricula) != re.sub(r"\W", "", registro.registro):
                continue
            resultados.append((candidato, registro))
    if not resultados:
        return {**publico, "estado_consulta": "fuente_foro_no_disponible" if fallos else "sin_registro_foro"}
    if fallos:
        return {**publico, "estado_consulta": "verificacion_incompleta", "resultados": [_respuesta_foro(publico, c, r) for c, r in resultados]}
    if len(resultados) > 1:
        return {**publico, "estado_consulta": "multiples_coincidencias_foro", "resultados": [_respuesta_foro(publico, c, r) for c, r in resultados]}
    candidato, registro = resultados[0]
    respuesta = {
        **publico,
        "estado_consulta": "completa",
        "nombres": nombres,
        "apellidos": f"{apellido_paterno} {apellido_materno}".strip() or None,
        "ciudad": publico.get("canton") or publico.get("provincia"),
        "cedula": candidato.cedula,
        "correo": registro.correo,
        "telefono_domicilio": registro.telefono_domicilio,
        "direccion_domicilio": registro.direccion_domicilio,
        "telefono_oficina": registro.telefono_oficina,
        "direccion_oficina": registro.direccion_oficina,
        "celular": registro.celular,
    }
    _guardar_ficha(
        sesion, codigo, nombre, publico.get("canton") or publico.get("provincia"), candidato.cedula, registro.correo,
        registro.telefono_domicilio, registro.direccion_domicilio,
        registro.telefono_oficina, registro.direccion_oficina, registro.celular,
    )
    return respuesta


def _respuesta_foro(publico, candidato, registro) -> dict:
    return {
        **publico, "estado_consulta": "completa", "cedula": candidato.cedula,
        "matricula": registro.registro,
        "ciudad": publico.get("canton") or publico.get("provincia"),
        **{campo: getattr(registro, campo) for campo in (
            "correo", "celular", "telefono_domicilio", "telefono_oficina",
            "direccion_domicilio", "direccion_oficina",
        )},
    }
