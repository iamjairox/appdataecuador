"""Rutas: Jobs -- Modulo 10, `GET /jobs/{job_id}`.

Sobre `TrabajoOrquestador`/`AuditoriaEtapa` (Submodulos 9.6/9.10/9.15,
Modulo 9 congelado) via los servicios de aplicacion existentes -- nunca
se lee la tabla directamente."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from govdata.application.dto.job_estado_dto import JobEstadoDTO
from govdata.application.dto.trabajo_orquestador_dto import TrabajoOrquestadorDTO
from govdata.application.services.auditoria_orquestacion_service import AuditoriaOrquestacionService
from govdata.application.services.cola_trabajos_orquestador_service import (
    ColaTrabajosOrquestadorService,
)
from govdata.infrastructure.api.dependencies import get_sesion, verificar_api_key
from govdata.infrastructure.api.schemas.job import JobResponseSchema
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_auditoria_etapa_repository import (
    SqlAlchemyAuditoriaEtapaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_trabajo_orquestador_repository import (
    SqlAlchemyTrabajoOrquestadorRepository,
)

router = APIRouter(prefix="/jobs", tags=["Jobs"], dependencies=[Depends(verificar_api_key)])


@router.get(
    "/{job_id}",
    summary="Estado de un job (TrabajoOrquestador)",
    description="Estado, prioridad, politica, intentos, fechas y errores del trabajo, mas el "
    "detalle por etapa (Submodulo 9.10/9.15: inicio/fin/duracion/cantidad de registros/razon de "
    "omision por cada uno de los 8 pasos del Planificador).",
    response_model=JobResponseSchema,
    responses={404: {"description": "Job no encontrado"}, 422: {"description": "job_id no es un UUID valido"}},
)
def obtener_estado_job(job_id: UUID, sesion: Annotated[Session, Depends(get_sesion)]) -> JobResponseSchema:
    cola = ColaTrabajosOrquestadorService(SqlAlchemyTrabajoOrquestadorRepository(sesion))
    trabajo = cola.buscar_por_id(job_id)
    if trabajo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job no encontrado: {job_id}")

    auditoria = AuditoriaOrquestacionService(SqlAlchemyAuditoriaEtapaRepository(sesion))
    etapas = auditoria.listar_por_trabajo(str(trabajo.id))
    job_estado = JobEstadoDTO(trabajo=TrabajoOrquestadorDTO.desde_entidad(trabajo), etapas=etapas)
    return JobResponseSchema.desde_job_estado_dto(job_estado)
