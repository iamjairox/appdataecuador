"""Rutas: Funcionarios -- Modulo 10.

Cada endpoint delega en el servicio de aplicacion que YA CALCULA esa
informacion (Modulos 5/6/7/8, congelados) -- ver el mapeo completo en el
informe final del modulo."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.dto.resultado_validacion_abogado_dto import (
    ResultadoDirectorioAutorizadoDTO,
)
from govdata.application.services.auditoria_consulta_fuente_service import (
    AuditoriaConsultaFuenteService,
)
from govdata.application.services.auditoria_orquestacion_service import AuditoriaOrquestacionService
from govdata.application.services.cola_trabajos_orquestador_service import (
    ColaTrabajosOrquestadorService,
)
from govdata.application.use_cases.validar_abogado_use_case import ValidarAbogadoUseCase
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.infrastructure.api.dependencies import get_container, get_sesion, verificar_api_key
from govdata.infrastructure.api.schemas.alerta import AlertaFuncionarioResponseSchema
from govdata.infrastructure.api.schemas.funcionario import PerfilConsolidadoResponseSchema
from govdata.infrastructure.api.schemas.perfil import (
    PerfilAcademicoResponseSchema,
    TimelineResponseSchema,
    VersionHistorialSchema,
)
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel
from govdata.infrastructure.persistence.postgresql.models.funcionario_model import FuncionarioModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_auditoria_etapa_repository import (
    SqlAlchemyAuditoriaEtapaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_consulta_fuente_log_repository import (
    SqlAlchemyConsultaFuenteLogRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
    SqlAlchemyPersonaMasterRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_trabajo_orquestador_repository import (
    SqlAlchemyTrabajoOrquestadorRepository,
)
from govdata.infrastructure.scraping.playwright.consulta_ecuador_adapter import (
    ConsultaEcuadorAsyncAdapter,
    SelectoresConsultaEcuador,
)

router = APIRouter(prefix="/funcionarios", tags=["Funcionarios"], dependencies=[Depends(verificar_api_key)])


def _resolver_persona_master(persona_master_id: int, sesion: Session) -> PersonaMaster:
    persona_master = SqlAlchemyPersonaMasterRepository(sesion).buscar_por_id(persona_master_id)
    if persona_master is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Funcionario no encontrado: {persona_master_id}",
        )
    return persona_master


@router.get(
    "/{persona_master_id}",
    summary="Perfil consolidado del funcionario",
    description="Forma EXACTA de `PerfilConsolidadoDTO` (Submodulo 8.10) -- `PerfilConsolidadoService` "
    "(Modulo 8, congelado), NUNCA reconstruido a mano.",
    response_model=PerfilConsolidadoResponseSchema,
    responses={404: {"description": "Funcionario no encontrado"}},
)
def obtener_perfil_consolidado(
    persona_master_id: int, sesion: Annotated[Session, Depends(get_sesion)],
) -> PerfilConsolidadoResponseSchema:
    # `PersonaMasterInvalidaError` (si no existe) se deja propagar al
    # manejador global (`exception_handlers.py`) -- ya la mapea a 404.
    perfil = get_container().crear_perfil_consolidado_service(sesion).construir_perfil(persona_master_id)
    return PerfilConsolidadoResponseSchema.model_validate(perfil)


@router.get(
    "/{persona_master_id}/historial",
    summary="Historial laboral del funcionario",
    description="`VersionFuncionario` (Modulo 5, `HistorialService.historial_de_persona`, "
    "REUTILIZADO) -- toda la trayectoria (cualquier entidad/cargo), mas antigua primero.",
    response_model=list[VersionHistorialSchema],
    responses={404: {"description": "Funcionario no encontrado"}},
)
def obtener_historial_funcionario(
    persona_master_id: int, sesion: Annotated[Session, Depends(get_sesion)],
) -> list[VersionHistorialSchema]:
    persona_master = _resolver_persona_master(persona_master_id, sesion)
    historial_service = get_container().crear_historial_service(sesion)
    versiones = historial_service.historial_de_persona(persona_master.persona_id)
    return [VersionHistorialSchema.model_validate(v) for v in versiones]


@router.get(
    "/{persona_master_id}/academico",
    summary="Informacion academica (SENESCYT) ya persistida",
    description="Forma EXACTA de `PerfilAcademicoDTO` (Submodulo 7.16) -- `PerfilAcademicoService` "
    "(Modulo 7, congelado).",
    response_model=PerfilAcademicoResponseSchema,
    responses={404: {"description": "Funcionario no encontrado"}},
)
def obtener_perfil_academico(
    persona_master_id: int, sesion: Annotated[Session, Depends(get_sesion)],
) -> PerfilAcademicoResponseSchema:
    perfil = get_container().crear_perfil_academico_service(sesion).construir_perfil(persona_master_id)
    return PerfilAcademicoResponseSchema.model_validate(perfil)


@router.get(
    "/{persona_master_id}/foro",
    summary="Informacion profesional (Foro de Abogados) ya persistida",
    description="Recorte `.foro` del mismo `PerfilConsolidadoDTO` (Submodulo 8.10) -- Modulo 8, "
    "congelado. `null` si nunca se consulto o el Foro no tiene registro.",
    responses={404: {"description": "Funcionario no encontrado"}},
)
def obtener_perfil_foro(persona_master_id: int, sesion: Annotated[Session, Depends(get_sesion)]) -> dict:
    perfil = get_container().crear_perfil_consolidado_service(sesion).construir_perfil(persona_master_id)
    return perfil.foro


@router.post("/{persona_master_id}/validar-abogado", status_code=status.HTTP_202_ACCEPTED)
async def validar_abogado(persona_master_id: int, sesion: Annotated[Session, Depends(get_sesion)]) -> dict:
    """Valida internamente; nunca expone identificadores ni datos del Foro."""
    master = _resolver_persona_master(persona_master_id, sesion)
    persona = SqlAlchemyPersonaRepository(sesion).buscar_por_id(master.persona_id)
    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona no encontrada")
    fila = sesion.execute(
        select(FuncionarioModel, EntidadModel)
        .join(EntidadModel, EntidadModel.id == FuncionarioModel.entidad_id)
        .where(FuncionarioModel.persona_id == persona.id, FuncionarioModel.fecha_fin.is_(None))
        .order_by(FuncionarioModel.id.desc())
    ).first()
    if fila is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo vigente no encontrado")
    funcionario, entidad = fila
    resultado_autorizado = ResultadoDirectorioAutorizadoDTO(
        nombre=f"{persona.nombres} {persona.apellidos}".strip(), puesto=funcionario.cargo,
        unidad=funcionario.dependencia, ciudad=(entidad.metadata_extra or {}).get("ciudad"),
        telefono=persona.telefono, celular=None, correo=persona.correo,
    )
    caso = ValidarAbogadoUseCase(
        ConsultaEcuadorAsyncAdapter(SelectoresConsultaEcuador()),
        get_container().foro_abogados_adapter(),
        AuditoriaConsultaFuenteService(SqlAlchemyConsultaFuenteLogRepository(sesion)),
        ColaTrabajosOrquestadorService(SqlAlchemyTrabajoOrquestadorRepository(sesion)),
        AuditoriaOrquestacionService(SqlAlchemyAuditoriaEtapaRepository(sesion)),
    )
    job_id, resultado = await caso.ejecutar(persona_master_id, persona)
    return {"job_id": job_id, "estado": resultado.estado.value, "resultado": resultado_autorizado.to_dict()}


@router.get(
    "/{persona_master_id}/alertas",
    summary="Alertas del funcionario (identidad + academico + Foro)",
    description="Agrega `AlertaPerfil` (Modulo 6) + `AlertaAcademica` (Modulo 7) + `AlertaForo` "
    "(Modulo 8) -- ningun servicio existente las junta, ver `AlertaFuncionarioDTO` (Modulo 10).",
    response_model=list[AlertaFuncionarioResponseSchema],
    responses={404: {"description": "Funcionario no encontrado"}},
)
def obtener_alertas_funcionario(
    persona_master_id: int, sesion: Annotated[Session, Depends(get_sesion)],
) -> list[AlertaFuncionarioResponseSchema]:
    _resolver_persona_master(persona_master_id, sesion)
    alertas = get_container().crear_obtener_alertas_funcionario_use_case(sesion).ejecutar(persona_master_id)
    return [AlertaFuncionarioResponseSchema.model_validate(a) for a in alertas]


@router.get(
    "/{persona_master_id}/timeline",
    summary="Timeline consolidado del funcionario",
    description="Forma de `TimelinePersonaDTO` (Submodulo 6.5) -- `TimelinePersonaService` "
    "(Modulo 6, congelado), une historial institucional + fuentes externas en una sola linea de "
    "tiempo.",
    response_model=TimelineResponseSchema,
    responses={404: {"description": "Funcionario no encontrado"}},
)
def obtener_timeline_funcionario(
    persona_master_id: int, sesion: Annotated[Session, Depends(get_sesion)],
) -> TimelineResponseSchema:
    persona_master = _resolver_persona_master(persona_master_id, sesion)
    timeline_service = get_container().crear_timeline_persona_service(sesion)
    timeline = timeline_service.construir(persona_master)
    return TimelineResponseSchema.model_validate(timeline)
