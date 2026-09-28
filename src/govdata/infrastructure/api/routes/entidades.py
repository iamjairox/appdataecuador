"""Rutas: Entidades -- Modulo 10.

Reglas de arquitectura (Submodulo 10.28, OBLIGATORIAS): `/consulta`,
`/actualizar` y `/consulta-masiva` usan EXCLUSIVAMENTE
`GovDataPipelineOrchestrator` (Modulo 9, congelado) -- esta capa nunca
llama descubrimiento/descarga/extraccion/SENESCYT/Foro por separado."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterator
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from govdata.application.dto.alerta_dto import AlertaDTO
from govdata.application.dto.filtros_entidad_listado_dto import FiltrosEntidadListadoDTO
from govdata.application.dto.filtros_funcionario_listado_dto import FiltrosFuncionarioListadoDTO
from govdata.application.dto.funcionario_listado_dto import FuncionarioListadoDTO
from govdata.application.services.govdata_pipeline_orchestrator import GovDataPipelineOrchestrator
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

router = APIRouter(prefix="/entidades", tags=["Entidades"], dependencies=[Depends(verificar_api_key)])

_COLUMNAS_CSV = (
    "nombre_completo", "nombres", "apellidos", "cedula", "cargo", "dependencia",
    "correo", "telefono", "registro_foro", "estado_foro", "provincia_foro",
)


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
