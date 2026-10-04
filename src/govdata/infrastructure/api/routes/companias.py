"""Directorio local de compañías de Supercias y verificación puntual de representantes."""
from __future__ import annotations

from datetime import UTC, datetime
import re
from threading import Lock
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import requests
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from govdata.application.dto.identificacion_cedula_dto import EstadoMatchingCedula
from govdata.application.services.consulta_cedula_cascada import consultar_cedula_en_cascada
from govdata.application.services.progreso_companias_service import progreso_companias
from govdata.domain.exceptions.domain_exceptions import GovDataError
from govdata.domain.rules.matching_cedula import hacer_matching_cedula
from govdata.infrastructure.api.dependencies import get_sesion
from govdata.infrastructure.persistence.postgresql.models.compania_model import CompaniaModel, RepresentanteCompaniaModel
from govdata.infrastructure.scraping.playwright.foro_abogados_adapter import ForoAbogadosPlaywrightAdapter
from govdata.infrastructure.scraping.playwright.fuentes_cedula import fuentes_consulta_cedula

router = APIRouter(prefix="/companias", tags=["Compañías Supercias"])
URL_EXCEL = "https://mercadodevalores.supercias.gob.ec/reportes/excel/directorio_companias.xlsx"
URL_DIRECTORIO = "https://mercadodevalores.supercias.gob.ec/reportes/directorioCompanias.jsf"
_carga_lock = Lock()


def _normalizar(texto: str) -> str:
    return " ".join("".join(c for c in unicodedata.normalize("NFD", str(texto)) if unicodedata.category(c) != "Mn").upper().split())


def _texto(valor: object) -> str | None:
    if valor is None: return None
    texto = str(valor).strip()
    return texto if texto and texto.lower() != "nan" else None


def _columna(fila: dict[str, object], *nombres: str) -> str | None:
    for nombre in nombres:
        valor = fila.get(nombre)
        if (texto := _texto(valor)) is not None: return texto
    return None


def _es_juridica(nombre: str | None, ciiu: str | None) -> bool:
    texto = _normalizar(f"{nombre or ''} {ciiu or ''}")
    return bool(re.search(r"\bM69(10|20)|JURID|ABOGAD|LEGAL|TRIBUT|AUDIT|CONTAB|NOTARI", texto))


def _direccion(fila: dict[str, object]) -> str | None:
    partes = [_columna(fila, campo) for campo in ("CALLE", "NÚMERO", "INTERSECCIÓN", "BARRIO")]
    return ", ".join(parte for parte in partes if parte) or None


def _valor_celda(celdas: list[str], indice: int) -> str | None:
    return _texto(celdas[indice]) if len(celdas) > indice else None


def _version_oficial_supercias() -> str:
    """Lee la fecha publicada por Supercias sin descargar el directorio completo."""
    respuesta = requests.get(URL_DIRECTORIO, timeout=60)
    respuesta.raise_for_status()
    contenido = respuesta.content.decode("latin-1", errors="ignore")
    coincidencia = re.search(
        r"FECHA\s+DE\s+ACTUALIZACI[^<]*</label>\s*</td>\s*<td>\s*<label[^>]*>\s*([^<]+)",
        contenido,
        re.IGNORECASE,
    )
    if not coincidencia:
        raise RuntimeError("Supercias no publicó la fecha de actualización del directorio")
    return " ".join(coincidencia.group(1).split())


async def _consultar_sri(ruc: str) -> dict[str, str | None]:
    """Consulta pública, individual y sin credenciales del RUC seleccionado."""
    url = "https://srienlinea.sri.gob.ec/sri-en-linea/SriRucWeb/ConsultaRuc/Consultas/consultaRuc"
    async with async_playwright() as playwright:
        navegador = await playwright.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )
        try:
            pagina = await navegador.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
                )
            )
            pagina.set_default_timeout(60_000)
            await pagina.goto(url, wait_until="domcontentloaded", timeout=120_000)
            await pagina.locator("#busquedaRucId").fill(ruc)
            await pagina.get_by_role("button", name="Consultar").click()
            await pagina.get_by_text("Actividad económica principal").wait_for(timeout=60_000)
            texto = await pagina.locator("body").inner_text()
        finally:
            await navegador.close()
    representante = re.search(r"Representante legal\s+Nombre/Razón Social:\s+(.+?)\s+Identificación:\s+([0-9]+)", texto, re.S)
    actividad = re.search(r"Actividad económica principal\s+(.+?)\s+Tipo contribuyente", texto, re.S)
    return {
        "representante": " ".join(representante.group(1).split()) if representante else None,
        "cedula": representante.group(2) if representante else None,
        "actividad": " ".join(actividad.group(1).split()) if actividad else None,
    }


@router.get("/estado")
def estado_directorio(sesion: Session = Depends(get_sesion)) -> dict:
    total = sesion.scalar(select(func.count()).select_from(CompaniaModel)) or 0
    ultima = sesion.scalar(select(func.max(CompaniaModel.cargado_en)))
    periodo = sesion.scalar(select(CompaniaModel.periodo_fuente).order_by(CompaniaModel.cargado_en.desc()).limit(1))
    return {"total": total, "ultima_carga": ultima, "periodo_fuente": periodo, "url_excel": URL_EXCEL}


@router.get("/progreso-carga")
def progreso_carga() -> dict[str, int | str | None]:
    """Progreso observable desde la interfaz mientras se importa el Excel."""
    return progreso_companias.obtener()


@router.post("/actualizar-directorio")
def actualizar_directorio(
    forzar: bool = True,
    sesion: Session = Depends(get_sesion),
) -> dict:
    """Descarga el Excel oficial una sola vez y lo deja disponible localmente."""
    if not _carga_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Ya hay una actualización del directorio en curso")

    # Supercias entrega una hoja de portada a clientes no navegadores aunque
    # conserve el nombre y tamaño del Excel. Se usa la tabla pública que el
    # mismo portal muestra al usuario, paginada de 1.000 filas.
    progreso_companias.iniciar_descarga()
    try:
        version_fuente = _version_oficial_supercias()
        ultima_version = sesion.scalar(
            select(CompaniaModel.periodo_fuente)
            .where(CompaniaModel.periodo_fuente.is_not(None))
            .order_by(CompaniaModel.cargado_en.desc())
            .limit(1)
        )
        if not forzar and ultima_version == version_fuente:
            total_actual = sesion.scalar(select(func.count()).select_from(CompaniaModel)) or 0
            progreso_companias.completar(total_actual)
            return {
                "actualizado": False,
                "motivo": "Supercias no ha publicado una versión más reciente",
                "total_importadas": total_actual,
                "periodo_fuente": version_fuente,
            }
        with sync_playwright() as playwright:
            navegador = playwright.chromium.launch(headless=True)
            try:
                pagina = navegador.new_page()
                pagina.goto(URL_DIRECTORIO, wait_until="networkidle", timeout=120_000)
                pagina.locator("select.ui-paginator-rpp-options").select_option("1000")
                pagina.wait_for_function(
                    "() => document.querySelectorAll('tbody.ui-datatable-data tr').length === 1000",
                    timeout=60_000,
                )
                total_filas = int(pagina.locator(".ui-paginator-current").inner_text().split(" de ")[1].split()[0])
                progreso_companias.iniciar_procesamiento(total_filas)
                ahora = datetime.now(UTC)
                total_importadas = 0
                for inicio in range(0, total_filas, 1000):
                    filas = pagina.locator("tbody.ui-datatable-data tr").evaluate_all(
                        "filas => filas.map(fila => Array.from(fila.cells, celda => celda.innerText.trim()))"
                    )
                    lote: list[dict] = []
                    for celdas in filas:
                        ruc, nombre = _valor_celda(celdas, 2), _valor_celda(celdas, 3)
                        if not ruc or not nombre:
                            continue
                        ciiu6 = _valor_celda(celdas, 21)
                        direccion = ", ".join(filter(None, (_valor_celda(celdas, i) for i in (12, 13, 14, 15)))) or None
                        lote.append({"ruc": ruc, "expediente": _valor_celda(celdas, 1), "nombre": nombre, "situacion_legal": _valor_celda(celdas, 4), "provincia": _valor_celda(celdas, 9), "canton": _valor_celda(celdas, 10), "ciudad": _valor_celda(celdas, 11), "direccion": direccion, "telefono": _valor_celda(celdas, 16), "representante": _valor_celda(celdas, 17), "cargo_representante": _valor_celda(celdas, 18), "ciiu_nivel_1": _valor_celda(celdas, 20), "ciiu_nivel_6": ciiu6, "es_juridica": _es_juridica(nombre, ciiu6), "periodo_fuente": version_fuente, "cargado_en": ahora})
                    if lote:
                        # El directorio oficial puede repetir el mismo RUC en
                        # una página. PostgreSQL no permite actualizar dos
                        # veces esa clave dentro de un solo INSERT ... UPSERT.
                        lote_unico = list({empresa["ruc"]: empresa for empresa in lote}.values())
                        sentencia = insert(CompaniaModel).values(lote_unico)
                        actualizables = {campo: getattr(sentencia.excluded, campo) for campo in lote_unico[0] if campo != "ruc"}
                        sesion.execute(sentencia.on_conflict_do_update(index_elements=[CompaniaModel.ruc], set_=actualizables))
                        sesion.commit()
                        total_importadas += len(lote_unico)
                    progreso_companias.actualizar(min(inicio + len(filas), total_filas), total_importadas)
                    if inicio + 1000 < total_filas:
                        anterior = pagina.locator("tbody.ui-datatable-data tr").first.locator("td").first.inner_text()
                        pagina.locator("a.ui-paginator-next").click()
                        pagina.wait_for_function(
                            "anterior => document.querySelector('tbody.ui-datatable-data tr td')?.innerText.trim() !== anterior",
                            arg=anterior,
                            timeout=60_000,
                        )
            finally:
                navegador.close()
        if not total_importadas:
            raise RuntimeError("La tabla oficial no devolvió compañías para importar")
        progreso_companias.completar(total_importadas)
        return {"actualizado": True, "total_importadas": total_importadas, "periodo_fuente": version_fuente}
    except Exception as error:
        progreso_companias.fallar(f"No se pudo actualizar el directorio: {str(error)[:240]}")
        raise
    finally:
        _carga_lock.release()


@router.get("")
def listar_companias(q: str | None = None, ruc: str | None = None, provincia: str | None = None, representante: str | None = None, solo_juridicas: bool = False, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), sesion: Session = Depends(get_sesion)) -> dict:
    consulta = select(CompaniaModel)
    if q: consulta = consulta.where(CompaniaModel.nombre.ilike(f"%{q.strip()}%"))
    if ruc: consulta = consulta.where(CompaniaModel.ruc.ilike(f"%{ruc.strip()}%"))
    if provincia: consulta = consulta.where(CompaniaModel.provincia.ilike(f"%{provincia.strip()}%"))
    if representante: consulta = consulta.where(CompaniaModel.representante.ilike(f"%{representante.strip()}%"))
    if solo_juridicas: consulta = consulta.where(CompaniaModel.es_juridica.is_(True))
    total = sesion.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    items = sesion.scalars(consulta.order_by(CompaniaModel.nombre).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [{"ruc": x.ruc, "nombre": x.nombre, "situacion_legal": x.situacion_legal, "provincia": x.provincia, "ciudad": x.ciudad, "direccion": x.direccion, "telefono": x.telefono, "representante": x.representante, "cargo_representante": x.cargo_representante, "ciiu": x.ciiu_nivel_6, "es_juridica": x.es_juridica} for x in items], "total": total, "page": page, "page_size": page_size}


@router.get("/consultados")
def companias_consultadas(sesion: Session = Depends(get_sesion)) -> dict:
    filas = sesion.execute(
        select(CompaniaModel, RepresentanteCompaniaModel)
        .join(RepresentanteCompaniaModel, RepresentanteCompaniaModel.compania_id == CompaniaModel.id)
        .order_by(RepresentanteCompaniaModel.consultado_en.desc())
    ).all()
    return {"items": [{
        "empresa": empresa.nombre, "ruc": empresa.ruc, "actividad": ficha.actividad_economica,
        "contacto": empresa.telefono, "ubicacion": ", ".join(filter(None, [empresa.direccion, empresa.ciudad, empresa.provincia])) or None,
        "representante": ficha.nombre, "cedula": ficha.cedula, "correo": ficha.correo, "celular": ficha.celular,
        "telefono_domicilio": ficha.telefono_domicilio, "telefono_oficina": ficha.telefono_oficina,
        "direccion_domicilio": ficha.direccion_domicilio, "direccion_oficina": ficha.direccion_oficina,
        "estado": ficha.estado, "consultado_en": ficha.consultado_en,
    } for empresa, ficha in filas]}


def _partes_representante(nombre: str) -> tuple[str, str, str]:
    partes = nombre.split()
    if len(partes) >= 4: return " ".join(partes[2:]), partes[0], partes[1]
    return nombre, "", ""


@router.post("/{ruc}/verificar-representante")
async def verificar_representante(ruc: str, sesion: Session = Depends(get_sesion)) -> dict:
    compania = sesion.scalar(select(CompaniaModel).where(CompaniaModel.ruc == ruc))
    if compania is None: raise HTTPException(status_code=404, detail="Compañía no encontrada")
    try:
        sri = await _consultar_sri(ruc)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"No fue posible consultar el RUC seleccionado en SRI: {str(error)[:160]}") from error
    representante = sri["representante"] or compania.representante
    if not representante: raise HTTPException(status_code=422, detail="La compañía no tiene representante en Supercias ni en SRI")
    cedula = sri["cedula"]
    if not cedula:
        nombres, paterno, materno = _partes_representante(representante)
        try:
            candidatos = await consultar_cedula_en_cascada(fuentes_consulta_cedula(), nombres, paterno, materno)
        except GovDataError:
            return {"estado": "source_unavailable", "empresa": compania.nombre, "ruc": compania.ruc, "actividad": sri["actividad"], "representante": representante}
        match = hacer_matching_cedula(nombres, f"{paterno} {materno}".strip(), candidatos)
        if match.estado not in {EstadoMatchingCedula.MATCH_EXACT, EstadoMatchingCedula.MATCH_HIGH_CONFIDENCE} or match.candidato is None:
            return {"estado": match.estado.value, "empresa": compania.nombre, "ruc": compania.ruc, "actividad": sri["actividad"], "representante": representante}
        cedula = match.candidato.cedula
    registros = await ForoAbogadosPlaywrightAdapter().buscar_por_cedula(cedula)
    registro = registros[0] if registros else None
    ficha = sesion.scalar(select(RepresentanteCompaniaModel).where(RepresentanteCompaniaModel.compania_id == compania.id))
    if ficha is None:
        ficha = RepresentanteCompaniaModel(compania_id=compania.id, nombre=representante)
        sesion.add(ficha)
    ficha.nombre = representante; ficha.actividad_economica = sri["actividad"] or f"CIIU registrado: {compania.ciiu_nivel_6 or compania.ciiu_nivel_1 or 'No disponible'}"; ficha.cedula = cedula; ficha.correo = registro.correo if registro else None; ficha.celular = registro.celular if registro else None
    ficha.telefono_domicilio = registro.telefono_domicilio if registro else None; ficha.telefono_oficina = registro.telefono_oficina if registro else None
    ficha.direccion_domicilio = registro.direccion_domicilio if registro else None; ficha.direccion_oficina = registro.direccion_oficina if registro else None
    ficha.estado = "completa" if registro else "sin_registro_foro"; ficha.consultado_en = datetime.now(UTC)
    return {"estado": ficha.estado, "empresa": compania.nombre, "ruc": compania.ruc, "actividad": ficha.actividad_economica, "contacto": compania.telefono, "ubicacion": ", ".join(filter(None, [compania.direccion, compania.ciudad, compania.provincia])) or None, "representante": ficha.nombre, "cedula": ficha.cedula, "correo": ficha.correo, "celular": ficha.celular, "telefono_domicilio": ficha.telefono_domicilio, "telefono_oficina": ficha.telefono_oficina, "direccion_domicilio": ficha.direccion_domicilio, "direccion_oficina": ficha.direccion_oficina}
