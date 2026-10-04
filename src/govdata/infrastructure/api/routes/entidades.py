"""Rutas: Entidades -- Modulo 10.

Reglas de arquitectura (Submodulo 10.28, OBLIGATORIAS): `/consulta`,
`/actualizar` y `/consulta-masiva` usan EXCLUSIVAMENTE
`GovDataPipelineOrchestrator` (Modulo 9, congelado) -- esta capa nunca
llama descubrimiento/descarga/extraccion/SENESCYT/Foro por separado."""

from __future__ import annotations

import csv
import io
import json
from threading import Lock
from dataclasses import asdict
from collections.abc import Iterator
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse
from sqlalchemy import String, func, select
from sqlalchemy.orm import Session
from types import SimpleNamespace
from govdata.infrastructure.persistence.postgresql.models.trabajo_orquestador_model import TrabajoOrquestadorModel
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador

from govdata.application.dto.alerta_dto import AlertaDTO
from govdata.application.dto.filtros_entidad_listado_dto import FiltrosEntidadListadoDTO
from govdata.application.dto.filtros_funcionario_listado_dto import FiltrosFuncionarioListadoDTO
from govdata.application.dto.funcionario_listado_dto import FuncionarioListadoDTO
from govdata.application.services.govdata_pipeline_orchestrator import GovDataPipelineOrchestrator
from govdata.application.services.progreso_listado_service import progreso_listados
from govdata.domain.entities.documento import EstadoDocumento
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.infrastructure.api.dependencies import (
    ParametrosPaginacion,
    get_container,
    get_orquestador,
    get_sesion,
    verificar_api_key,
)
from govdata.infrastructure.api.schemas.alerta import AlertaResponseSchema
from govdata.infrastructure.api.schemas.cambio import CambioResponseSchema
from govdata.infrastructure.api.schemas.common import PaginaSchema
from govdata.infrastructure.api.schemas.consulta import ConsultaEntidadResponseSchema
from govdata.infrastructure.api.schemas.entidad import EntidadResponseSchema
from govdata.infrastructure.api.schemas.funcionario import FuncionarioResponseSchema
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_repository import (
    SqlAlchemyAlertaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_entidad_repository import (
    SqlAlchemyEntidadRepository,
)
from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel
from govdata.infrastructure.persistence.postgresql.models.funcionario_model import FuncionarioModel
from govdata.infrastructure.persistence.postgresql.models.publicacion_model import PublicacionModel
from govdata.infrastructure.persistence.postgresql.models.verificacion_model import VerificacionModel
from govdata.infrastructure.persistence.postgresql.models.persona_master_model import PersonaMasterModel
from govdata.infrastructure.persistence.postgresql.models.consulta_foro_model import ConsultaForoModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)

router = APIRouter(prefix="/entidades", tags=["Entidades"], dependencies=[Depends(verificar_api_key)])

# La actualización del listado puede durar varios minutos para entidades
# grandes. Evita que un reintento del navegador inicie una segunda extracción
# concurrente de la misma entidad mientras la primera sigue en curso.
_listados_en_progreso: set[int] = set()
_lock_listados_en_progreso = Lock()

_COLUMNAS_CSV = (
    "nombre_completo", "nombres", "apellidos", "cedula", "cargo", "dependencia",
    "correo", "telefono", "extension_telefonica", "registro_foro", "estado_foro", "provincia_foro",
)


class MarcarProfesionalesRequest(BaseModel):
    funcionario_ids: list[int] = Field(min_length=1, max_length=100)


def _resolver_nombre_entidad(entidad_id: int, sesion: Session) -> str:
    entidad = SqlAlchemyEntidadRepository(sesion).buscar_por_id(entidad_id)
    if entidad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entidad no encontrada: {entidad_id}")
    return entidad.nombre


@router.get(
    "",
    summary="Listar entidades",
    description="Lista entidades disponibles (Modulo 2, ya descubiertas). Filtros opcionales: "
    "nombre, provincia, ciudad, tipo_institucion, portal_origen. `provincia`/`ciudad` se aceptan "
    "pero hoy no filtran nada real -- Transparencia no captura esa informacion (ver Submodulo 4.7).",
    response_model=PaginaSchema[EntidadResponseSchema],
)
def listar_entidades(
    sesion: Annotated[Session, Depends(get_sesion)],
    paginacion: Annotated[ParametrosPaginacion, Depends()],
    nombre: str | None = None,
    provincia: str | None = None,
    ciudad: str | None = None,
    tipo_institucion: str | None = None,
    portal_origen: str | None = None,
) -> PaginaSchema[EntidadResponseSchema]:
    caso_uso = get_container().crear_listar_entidades_api_use_case(sesion)
    filtros = FiltrosEntidadListadoDTO(
        nombre=nombre, provincia=provincia, ciudad=ciudad,
        tipo_institucion=tipo_institucion, portal_origen=portal_origen,
    )
    pagina = caso_uso.ejecutar(filtros, paginacion.page, paginacion.page_size)
    return PaginaSchema.desde_pagina_dto(pagina, EntidadResponseSchema)


@router.get(
    "/{entidad_id}",
    summary="Detalle de una entidad",
    response_model=EntidadResponseSchema,
    responses={404: {"description": "Entidad no encontrada"}},
)
def obtener_entidad(entidad_id: int, sesion: Annotated[Session, Depends(get_sesion)]) -> EntidadResponseSchema:
    caso_uso = get_container().crear_listar_entidades_api_use_case(sesion)
    entidad = caso_uso.obtener_por_id(entidad_id)
    if entidad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entidad no encontrada: {entidad_id}")
    return EntidadResponseSchema.model_validate(entidad)


@router.get(
    "/{entidad_id}/consulta",
    summary="Consultar entidad (operacion 'un clic')",
    description="EL endpoint principal (Submodulo 10.6): ejecuta el pipeline completo via "
    "`GovDataPipelineOrchestrator` -- Transparencia -> deteccion de cambios -> SENESCYT -> Foro -> "
    "perfil consolidado, aprovechando cache/monitoreo existentes (nunca repite trabajo innecesario). "
    "`politica` por defecto: `consulta_rapida`.",
    response_model=ConsultaEntidadResponseSchema,
    responses={404: {"description": "Entidad no encontrada"}},
)
def consultar_entidad(
    entidad_id: int,
    orquestador: Annotated[GovDataPipelineOrchestrator, Depends(get_orquestador)],
    sesion: Annotated[Session, Depends(get_sesion)],
    politica: str = Query(default="consulta_rapida", description="consulta_rapida | actualizacion_completa | solo_cambios | masiva_nocturna"),
) -> ConsultaEntidadResponseSchema:
    nombre = _resolver_nombre_entidad(entidad_id, sesion)
    resultado = orquestador.consultar_entidad(nombre, politica=politica)
    return ConsultaEntidadResponseSchema.model_validate(resultado)


@router.post(
    "/{entidad_id}/funcionarios/actualizar-listado",
    summary="Actualizar solo el listado institucional de funcionarios",
    description="Ejecuta Transparencia → descarga → extracción. No consulta SENESCYT, Foro ni otras fuentes externas.",
)
def actualizar_listado_institucional(
    entidad_id: int,
    sesion: Annotated[Session, Depends(get_sesion)],
) -> dict:
    entidad = SqlAlchemyEntidadRepository(sesion).buscar_por_id(entidad_id)
    if entidad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entidad no encontrada: {entidad_id}")
    with _lock_listados_en_progreso:
        if entidad_id in _listados_en_progreso:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El listado institucional de esta entidad ya se está procesando.",
            )
        _listados_en_progreso.add(entidad_id)
    try:
        progreso_listados.iniciar(entidad_id)
        # "Consultar listado" debe servir el directorio vigente ya
        # persistido. Solo descarga/extrae si no existe una versión utilizable;
        # forzar una reextracción en cada clic hacía que listados grandes se
        # procesaran desde cero una y otra vez.
        resultado = get_container().crear_consulta_service(sesion).consultar_entidad(entidad)
        progreso_listados.completar(entidad_id, len(resultado.funcionarios))
        return asdict(resultado)
    except Exception:
        progreso_listados.fallar(entidad_id, "No se pudo completar el listado institucional.")
        raise
    finally:
        with _lock_listados_en_progreso:
            _listados_en_progreso.discard(entidad_id)


@router.get(
    "/{entidad_id}/funcionarios/progreso-listado",
    summary="Progreso real del listado institucional",
)
def obtener_progreso_listado(entidad_id: int, sesion: Annotated[Session, Depends(get_sesion)]) -> dict:
    _resolver_nombre_entidad(entidad_id, sesion)
    return progreso_listados.obtener(entidad_id)


@router.get(
    "/{entidad_id}/funcionarios/estado-listado",
    summary="Estado del listado institucional persistido",
)
def obtener_estado_listado(entidad_id: int, sesion: Annotated[Session, Depends(get_sesion)]) -> dict:
    """Expone el período conocido y si hay una publicación pendiente de procesar."""
    _resolver_nombre_entidad(entidad_id, sesion)
    publicacion = sesion.scalar(
        select(PublicacionModel)
        .where(PublicacionModel.entidad_id == entidad_id)
        .order_by(PublicacionModel.mes_publicado.desc())
        .limit(1)
    )
    documento = (
        sesion.scalar(select(DocumentoModel).where(DocumentoModel.publicacion_id == publicacion.id))
        if publicacion is not None
        else None
    )
    total = sesion.scalar(
        select(func.count()).select_from(FuncionarioModel).where(
            FuncionarioModel.entidad_id == entidad_id,
            FuncionarioModel.fecha_fin.is_(None),
        )
    ) or 0
    # El estado pertenece al modelo ORM; ``esta_descargado`` solo existe en
    # la entidad de dominio y no está disponible aquí.
    requiere_actualizacion = documento is None or documento.estado != EstadoDocumento.DESCARGADO
    ultima_verificacion = sesion.scalar(
        select(VerificacionModel)
        .where(VerificacionModel.entidad_id == entidad_id)
        .order_by(VerificacionModel.verificado_en.desc())
        .limit(1)
    )
    total_juridicos = sesion.scalar(
        select(func.count()).select_from(FuncionarioModel).where(
            FuncionarioModel.entidad_id == entidad_id,
            FuncionarioModel.fecha_fin.is_(None),
            FuncionarioModel.area_clasificada == AreaRelevante.JURIDICA,
        )
    ) or 0
    total_consultados = sesion.scalar(
        select(func.count(func.distinct(FuncionarioModel.id)))
        .select_from(FuncionarioModel)
        .join(PersonaMasterModel, PersonaMasterModel.persona_id == FuncionarioModel.persona_id)
        .where(
            FuncionarioModel.entidad_id == entidad_id,
            FuncionarioModel.fecha_fin.is_(None),
            select(ConsultaForoModel.id).where(
                ConsultaForoModel.persona_master_id == PersonaMasterModel.id,
                ConsultaForoModel.finalizado_en.is_not(None),
            ).exists() | select(TrabajoOrquestadorModel.id).where(
                TrabajoOrquestadorModel.tipo == TipoTrabajoOrquestador.VALIDACION_ABOGADO,
                TrabajoOrquestadorModel.parametros["persona_master_id"].as_string() == func.cast(PersonaMasterModel.id, String),
                TrabajoOrquestadorModel.finalizado_en.is_not(None),
            ).exists(),
        )
    ) or 0
    return {
        "funcionarios_persistidos": total,
        "profesionales_juridicos": total_juridicos,
        "funcionarios_consultados": total_consultados,
        "periodo_publicacion": publicacion.mes_publicado if publicacion else None,
        "fecha_extraccion": documento.descargado_en if documento else None,
        "ultima_verificacion_dpe": ultima_verificacion.verificado_en if ultima_verificacion else None,
        "estado_verificacion_dpe": ultima_verificacion.motivo if ultima_verificacion else "aun_no_verificado",
        "requiere_actualizacion": requiere_actualizacion,
        "mensaje": (
            "Hay una publicación de Transparencia pendiente de procesar."
            if requiere_actualizacion
            else "El listado guardado corresponde a la última publicación conocida de Transparencia."
        ),
    }


@router.post(
    "/{entidad_id}/funcionarios/comprobar-publicacion-dpe",
    summary="Comprobar la última publicación en DPE sin descargar el listado",
)
def comprobar_publicacion_dpe(entidad_id: int, sesion: Annotated[Session, Depends(get_sesion)]) -> dict:
    """Consulta DPE y compara el período remoto con el listado guardado.

    Esta operación no descarga documentos ni extrae funcionarios. La hora
    guardada es la comprobación realizada por DataOK, no una hora inventada
    de DPE.
    """
    entidad = SqlAlchemyEntidadRepository(sesion).buscar_por_id(entidad_id)
    if entidad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entidad no encontrada: {entidad_id}")
    actual = sesion.scalar(
        select(PublicacionModel.mes_publicado)
        .where(PublicacionModel.entidad_id == entidad_id)
        .order_by(PublicacionModel.mes_publicado.desc())
        .limit(1)
    )
    descubrimiento = get_container().crear_descubrimiento_dpe()
    try:
        remoto = descubrimiento.descubrir(entidad)
    finally:
        descubrimiento.cerrar()
    if not remoto.exito or remoto.publicacion is None:
        return {
            "estado": "no_se_pudo_comprobar",
            "periodo_local": actual,
            "periodo_dpe": None,
            "mensaje": "No fue posible comprobar la última publicación en DPE.",
        }
    periodo_dpe = remoto.publicacion.mes_publicado
    hay_novedad = actual is None or periodo_dpe > actual
    return {
        "estado": "hay_publicacion_mas_reciente" if hay_novedad else "vigente",
        "periodo_local": actual,
        "periodo_dpe": periodo_dpe,
        "mensaje": (
            f"DPE tiene {periodo_dpe}; tu listado es {actual}."
            if hay_novedad else "Tu listado ya corresponde a la última publicación detectada en DPE."
        ),
    }


@router.post(
    "/{entidad_id}/actualizar",
    summary="Forzar actualizacion completa",
    description="Fuerza la politica `actualizacion_completa` (Submodulo 9.13) -- revisa "
    "Transparencia/SENESCYT/Foro aunque exista cache vigente. Ejecuta SINCRONAMENTE dentro de la "
    "peticion (mismo modelo que los scripts CLI existentes; no se introdujo un worker en segundo "
    "plano nuevo -- ver limitaciones del informe del Modulo 10).",
    response_model=ConsultaEntidadResponseSchema,
    responses={404: {"description": "Entidad no encontrada"}},
)
def actualizar_entidad(
    entidad_id: int,
    orquestador: Annotated[GovDataPipelineOrchestrator, Depends(get_orquestador)],
    sesion: Annotated[Session, Depends(get_sesion)],
) -> ConsultaEntidadResponseSchema:
    nombre = _resolver_nombre_entidad(entidad_id, sesion)
    resultado = orquestador.actualizar_entidad(nombre)
    return ConsultaEntidadResponseSchema.model_validate(resultado)


@router.post(
    "/consulta-masiva",
    summary="Consulta masiva de entidades activas",
    description="Reutiliza `GovDataPipelineOrchestrator.consultar_masivo` (concurrencia y "
    "reintentos gobernados por la politica -- nunca un motor paralelo nuevo).",
    response_model=list[ConsultaEntidadResponseSchema],
)
def consultar_masivo(
    orquestador: Annotated[GovDataPipelineOrchestrator, Depends(get_orquestador)],
    politica: str = Query(default="consulta_rapida"),
) -> list[ConsultaEntidadResponseSchema]:
    resultados = orquestador.consultar_masivo(politica=politica)
    return [ConsultaEntidadResponseSchema.model_validate(r) for r in resultados]


@router.post(
    "/actualizar-masivo",
    summary="Actualizacion masiva forzada (fuera de horario)",
    description="Fuerza `masiva_nocturna` (concurrencia limitada, prioriza pendientes, reintenta "
    "errores transitorios) via `GovDataPipelineOrchestrator.actualizar_masivo`.",
    response_model=list[ConsultaEntidadResponseSchema],
)
def actualizar_masivo(
    orquestador: Annotated[GovDataPipelineOrchestrator, Depends(get_orquestador)],
) -> list[ConsultaEntidadResponseSchema]:
    resultados = orquestador.actualizar_masivo()
    return [ConsultaEntidadResponseSchema.model_validate(r) for r in resultados]


@router.get(
    "/{entidad_id}/funcionarios",
    summary="Listar funcionarios de una entidad (solo datos ya persistidos)",
    description="NUNCA dispara descubrimiento/descarga/extraccion/SENESCYT/Foro -- solo lee "
    "`Persona`/`Funcionario` (Modulos 1/4) ya guardados. Para el perfil fusionado, usar "
    "`GET /funcionarios/{persona_master_id}`.",
    response_model=PaginaSchema[FuncionarioResponseSchema],
    responses={404: {"description": "Entidad no encontrada"}},
)
def listar_funcionarios_de_entidad(
    entidad_id: int,
    sesion: Annotated[Session, Depends(get_sesion)],
    paginacion: Annotated[ParametrosPaginacion, Depends()],
    nombre: str | None = None,
    apellido: str | None = None,
    cedula: str | None = None,
    cargo: str | None = None,
    dependencia: str | None = None,
    area: AreaRelevante | None = None,
    correo: str | None = None,
    telefono: str | None = None,
    solo_vigentes: bool = True,
) -> PaginaSchema[FuncionarioResponseSchema]:
    _resolver_nombre_entidad(entidad_id, sesion)
    repo = get_container().crear_funcionario_consulta_paginada_repository(sesion)
    filtros = FiltrosFuncionarioListadoDTO(
        nombre=nombre, apellido=apellido, cedula=cedula, cargo=cargo, dependencia=dependencia,
        area=area, correo=correo, telefono=telefono, solo_vigentes=solo_vigentes,
    )
    items, total = repo.buscar_paginado(entidad_id, filtros, paginacion.page, paginacion.page_size)
    return PaginaSchema[FuncionarioResponseSchema](
        items=[FuncionarioResponseSchema.model_validate(i) for i in items],
        page=paginacion.page, page_size=paginacion.page_size, total=total,
        pages=(total + paginacion.page_size - 1) // paginacion.page_size if paginacion.page_size else 0,
    )


def _ultimo_intento_externo(sesion: Session, master_id: int):
    foro = sesion.scalar(select(ConsultaForoModel).where(
        ConsultaForoModel.persona_master_id == master_id
    ).order_by(ConsultaForoModel.iniciado_en.desc()).limit(1))
    trabajo = sesion.scalar(select(TrabajoOrquestadorModel).where(
        TrabajoOrquestadorModel.tipo == TipoTrabajoOrquestador.VALIDACION_ABOGADO,
        TrabajoOrquestadorModel.parametros["persona_master_id"].as_string() == str(master_id),
    ).order_by(TrabajoOrquestadorModel.creado_en.desc()).limit(1))
    # Una identificación sin coincidencias termina antes de consultar Foro.
    # El trabajo persistido sigue siendo un intento real, no un pendiente.
    if trabajo is not None and (foro is None or (trabajo.iniciado_en and trabajo.iniciado_en > foro.iniciado_en)):
        return SimpleNamespace(
            iniciado_en=trabajo.iniciado_en or trabajo.creado_en,
            finalizado_en=trabajo.finalizado_en,
            exito=trabajo.estado.value == "completado",
            pagina_vacia=True,
            error=trabajo.ultimo_error,
        )
    return foro


@router.get("/{entidad_id}/funcionarios/estado-consulta", summary="Estados persistentes de consulta externa")
def estados_consulta_externa(entidad_id: int, sesion: Annotated[Session, Depends(get_sesion)]) -> dict:
    """Resume el último intento de Foro por profesional, sin consultar fuentes."""
    _resolver_nombre_entidad(entidad_id, sesion)
    filas = sesion.execute(
        select(FuncionarioModel.id, PersonaMasterModel.id)
        .join(PersonaMasterModel, PersonaMasterModel.persona_id == FuncionarioModel.persona_id, isouter=True)
        .where(
            FuncionarioModel.entidad_id == entidad_id,
            FuncionarioModel.fecha_fin.is_(None),
            FuncionarioModel.area_clasificada == AreaRelevante.JURIDICA,
        )
    ).all()
    estados: dict[str, dict] = {}
    for funcionario_id, master_id in filas:
        if master_id is None:
            estados[str(funcionario_id)] = {"estado": "pendiente", "fecha": None}
            continue
        ultimo = _ultimo_intento_externo(sesion, master_id)
        if ultimo is None:
            estado = "pendiente"
        elif ultimo.finalizado_en is None:
            estado = "en_proceso"
        elif ultimo.exito:
            estado = "sin_coincidencia" if ultimo.pagina_vacia else "completada"
        else:
            estado = "error"
        estados[str(funcionario_id)] = {"estado": estado, "fecha": (ultimo.finalizado_en or ultimo.iniciado_en) if ultimo else None, "error": ultimo.error if ultimo else None}
    return {"items": estados}


def _marcar_como_profesional_juridico(sesion: Session, entidad_id: int, funcionario_ids: list[int]) -> int:
    funcionarios = list(sesion.scalars(
        select(FuncionarioModel).where(
            FuncionarioModel.id.in_(funcionario_ids),
            FuncionarioModel.entidad_id == entidad_id,
            FuncionarioModel.fecha_fin.is_(None),
        )
    ))
    encontrados = {funcionario.id for funcionario in funcionarios}
    faltantes = set(funcionario_ids) - encontrados
    if faltantes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uno o más funcionarios vigentes no pertenecen a esta entidad")
    for funcionario in funcionarios:
        # Selección humana persistente: se incorpora al mismo grupo que el
        # clasificador automático, sin ejecutar ninguna fuente externa.
        funcionario.area_clasificada = AreaRelevante.JURIDICA
        funcionario.score_clasificacion = 1.0
    sesion.commit()
    return len(funcionarios)


@router.post(
    "/{entidad_id}/funcionarios/marcar-profesionales",
    summary="Agregar funcionarios seleccionados a profesionales jurídicos y afines",
)
def marcar_funcionarios_profesionales(
    entidad_id: int,
    solicitud: MarcarProfesionalesRequest,
    sesion: Annotated[Session, Depends(get_sesion)],
) -> dict:
    _resolver_nombre_entidad(entidad_id, sesion)
    return {"marcados": _marcar_como_profesional_juridico(sesion, entidad_id, solicitud.funcionario_ids)}


@router.post(
    "/{entidad_id}/funcionarios/{funcionario_id}/marcar-profesional",
    summary="Agregar un funcionario a profesionales jurídicos y afines",
)
def marcar_funcionario_profesional(
    entidad_id: int,
    funcionario_id: int,
    sesion: Annotated[Session, Depends(get_sesion)],
) -> dict:
    _resolver_nombre_entidad(entidad_id, sesion)
    _marcar_como_profesional_juridico(sesion, entidad_id, [funcionario_id])
    return {"funcionario_id": funcionario_id, "marcado": True}


@router.post(
    "/{entidad_id}/funcionarios/{funcionario_id}/preparar-consulta",
    summary="Preparar la identidad de un funcionario para consulta externa",
    responses={404: {"description": "Entidad o funcionario no encontrado"}},
)
def preparar_funcionario_para_consulta(
    entidad_id: int,
    funcionario_id: int,
    sesion: Annotated[Session, Depends(get_sesion)],
) -> dict:
    """Crea o reutiliza la identidad maestra al seleccionar un funcionario.

    La extracción institucional persiste Personas, pero no debe crear miles
    de identidades maestras que quizá nunca se consultarán. Este punto de
    entrada lo hace de forma individual, idempotente y justo antes de que el
    usuario pida consultar fuentes externas.
    """
    nombre_entidad = _resolver_nombre_entidad(entidad_id, sesion)
    funcionario = sesion.scalar(
        select(FuncionarioModel).where(
            FuncionarioModel.id == funcionario_id,
            FuncionarioModel.entidad_id == entidad_id,
            FuncionarioModel.fecha_fin.is_(None),
        )
    )
    if funcionario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionario vigente no encontrado")
    persona = SqlAlchemyPersonaRepository(sesion).buscar_por_id(funcionario.persona_id)
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona del funcionario no encontrada")

    master = get_container().crear_resolver_persona_master_use_case(sesion).ejecutar(
        persona,
        cargo=funcionario.cargo,
        institucion=nombre_entidad,
    )
    return {"funcionario_id": funcionario_id, "persona_master_id": master.id}


@router.get(
    "/{entidad_id}/funcionarios/consultados",
    summary="Listar funcionarios con datos externos ya consultados",
    description="Lee exclusivamente los datos persistidos de Foro; nunca dispara consultas externas."
)
def listar_funcionarios_consultados(
    entidad_id: int,
    sesion: Annotated[Session, Depends(get_sesion)],
    paginacion: Annotated[ParametrosPaginacion, Depends()],
) -> PaginaSchema[dict]:
    _resolver_nombre_entidad(entidad_id, sesion)
    repo = get_container().crear_funcionario_consulta_paginada_repository(sesion)
    # No se puede paginar primero el directorio institucional y filtrar
    # después: si un jurídico consultado está en la fila 350, desaparecía de
    # esta vista aunque su RegistroForo estuviera guardado. Un intento
    # finalizado sin coincidencia también es un resultado persistido y debe
    # mostrarse al usuario, no desaparecer como si nunca se hubiese consultado.
    _, total_institucional = repo.buscar_paginado(
        entidad_id, FiltrosFuncionarioListadoDTO(), page=1, page_size=1
    )
    perfil_service = get_container().crear_perfil_consolidado_service(sesion)
    consultados_todos: list[dict] = []
    tamano_lote = 500
    for pagina_institucional in range(1, (total_institucional + tamano_lote - 1) // tamano_lote + 1):
        items, _ = repo.buscar_paginado(
            entidad_id, FiltrosFuncionarioListadoDTO(), pagina_institucional, tamano_lote
        )
        for item in items:
            if item.persona_master_id is None:
                continue
            ultima_consulta = _ultimo_intento_externo(sesion, item.persona_master_id)
            if ultima_consulta is None or ultima_consulta.finalizado_en is None:
                continue
            registros = perfil_service.construir_foro(item.persona_master_id).get("registros", [])
            foro = registros[0] if registros else {}
            consultados_todos.append({
                **item.to_dict(),
                "registro_foro": foro.get("registro"),
                "estado_foro": foro.get("estado"),
                "provincia_foro": foro.get("provincia"),
                "correo_personal": foro.get("correo_personal"),
                "celular_personal": foro.get("celular_personal"),
                "fecha_consulta": foro.get("fecha_consulta") or ultima_consulta.finalizado_en,
                "estado_consulta_externa": (
                    "Completada" if registros else "Completada — sin datos externos encontrados"
                ) if ultima_consulta.exito else "Error al consultar fuentes externas",
            })
    total = len(consultados_todos)
    inicio = (paginacion.page - 1) * paginacion.page_size
    consultados = consultados_todos[inicio : inicio + paginacion.page_size]
    return PaginaSchema[dict](
        items=consultados, page=paginacion.page, page_size=paginacion.page_size,
        total=total, pages=(total + paginacion.page_size - 1) // paginacion.page_size if total else 0,
    )


@router.get(
    "/{entidad_id}/funcionarios/exportar",
    summary="Exportar funcionarios de una entidad (CSV o JSON)",
    description="Exporta desde BD (nunca vuelve a consultar Transparencia/SENESCYT/Foro), en "
    "streaming para no cargar todo en memoria (Submodulo 10.34).",
    responses={404: {"description": "Entidad no encontrada"}},
)
def exportar_funcionarios(
    entidad_id: int,
    sesion: Annotated[Session, Depends(get_sesion)],
    formato: str = Query(default="csv", pattern="^(csv|json)$"),
) -> StreamingResponse:
    _resolver_nombre_entidad(entidad_id, sesion)
    repo = get_container().crear_funcionario_consulta_paginada_repository(sesion)
    filtros = FiltrosFuncionarioListadoDTO()

    def _paginas() -> Iterator[list[FuncionarioListadoDTO]]:
        pagina = 1
        tamano = 200
        while True:
            items, total = repo.buscar_paginado(entidad_id, filtros, pagina, tamano)
            if not items:
                return
            yield items
            if pagina * tamano >= total:
                return
            pagina += 1

    if formato == "json":
        def _generar_json() -> Iterator[str]:
            yield "["
            primero = True
            for lote in _paginas():
                for item in lote:
                    yield ("" if primero else ",") + json.dumps(item.to_dict(), default=str)
                    primero = False
            yield "]"

        return StreamingResponse(
            _generar_json(), media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=funcionarios_entidad_{entidad_id}.json"},
        )

    def _generar_csv() -> Iterator[str]:
        buffer = io.StringIO()
        escritor = csv.DictWriter(buffer, fieldnames=_COLUMNAS_CSV, extrasaction="ignore")
        escritor.writeheader()
        yield buffer.getvalue()
        for lote in _paginas():
            buffer = io.StringIO()
            escritor = csv.DictWriter(buffer, fieldnames=_COLUMNAS_CSV, extrasaction="ignore")
            for item in lote:
                escritor.writerow(item.to_dict())
            yield buffer.getvalue()

    return StreamingResponse(
        _generar_csv(), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=funcionarios_entidad_{entidad_id}.csv"},
    )


@router.get(
    "/{entidad_id}/cambios",
    summary="Cambios detectados en el historial de la entidad",
    description="Fuente: `VersionFuncionario` (Modulo 5, `HistorialService`). `tipo_cambio`/"
    "`criticidad` se aceptan pero no filtran nada -- esa clasificacion no se persiste junto a la "
    "version (ver `Cambio EntidadDTO`); para verla YA CLASIFICADA usar `GET /entidades/{id}/alertas`.",
    response_model=PaginaSchema[CambioResponseSchema],
    responses={404: {"description": "Entidad no encontrada"}},
)
def obtener_cambios_entidad(
    entidad_id: int,
    sesion: Annotated[Session, Depends(get_sesion)],
    paginacion: Annotated[ParametrosPaginacion, Depends()],
    desde: date | None = None,
    hasta: date | None = None,
) -> PaginaSchema[CambioResponseSchema]:
    _resolver_nombre_entidad(entidad_id, sesion)
    caso_uso = get_container().crear_obtener_cambios_entidad_use_case(sesion)
    pagina = caso_uso.ejecutar(entidad_id, paginacion.page, paginacion.page_size, desde=desde, hasta=hasta)
    return PaginaSchema.desde_pagina_dto(pagina, CambioResponseSchema)


@router.get(
    "/{entidad_id}/alertas",
    summary="Alertas de la entidad",
    description="`Alerta` (Modulo 5, congelado) -- ya clasificada (tipo/prioridad) y persistida.",
    response_model=PaginaSchema[AlertaResponseSchema],
    responses={404: {"description": "Entidad no encontrada"}},
)
def obtener_alertas_entidad(
    entidad_id: int,
    sesion: Annotated[Session, Depends(get_sesion)],
    paginacion: Annotated[ParametrosPaginacion, Depends()],
) -> PaginaSchema[AlertaResponseSchema]:
    _resolver_nombre_entidad(entidad_id, sesion)
    alertas = sorted(
        (AlertaDTO.desde_entidad(a) for a in SqlAlchemyAlertaRepository(sesion).listar_por_entidad(entidad_id)),
        key=lambda a: a.detectado_en, reverse=True,
    )
    total = len(alertas)
    inicio = (paginacion.page - 1) * paginacion.page_size
    pagina_items = alertas[inicio : inicio + paginacion.page_size]
    return PaginaSchema[AlertaResponseSchema](
        items=[AlertaResponseSchema.model_validate(a) for a in pagina_items],
        page=paginacion.page, page_size=paginacion.page_size, total=total,
        pages=(total + paginacion.page_size - 1) // paginacion.page_size if paginacion.page_size else 0,
    )
