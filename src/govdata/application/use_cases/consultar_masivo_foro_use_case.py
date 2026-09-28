"""Caso de uso: ConsultarMasivoForoUseCase -- Submodulo 8.13 (Consulta
Masiva): "Debe reutilizar exactamente el mismo pipeline" (la consulta
individual, Submodulo 8.12) -- aqui se reutiliza `EnriquecimientoForoService`
(el mismo motor que usa `ConsultarPersonaForoUseCase`), operando sobre
todas las `PersonaMaster` activas (Modulo 6, `listar_activas`,
REUTILIZADO). Un item que falla NUNCA detiene a los demas -- mismo
principio que `EnriquecerMasivoAcademicoUseCase` (Modulo 7)."""

from __future__ import annotations

from govdata.application.dto.resultado_enriquecimiento_foro_dto import (
    ResultadoEnriquecimientoForoDTO,
)
from govdata.application.ports.persona_master_repository_port import PersonaMasterRepositoryPort
from govdata.application.ports.persona_repository_port import PersonaRepositoryPort
from govdata.application.services.enriquecimiento_foro_service import EnriquecimientoForoService
from govdata.application.services.job_manager_service import JobManagerService
from govdata.config.logging_config import get_logger
from govdata.domain.entities.job import JobStatus, TipoJob
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import GovDataError

logger = get_logger(__name__)


class ConsultarMasivoForoUseCase:
    def __init__(
        self,
        persona_master_repository: PersonaMasterRepositoryPort,
        persona_repository: PersonaRepositoryPort,
        enriquecimiento_foro_service: EnriquecimientoForoService,
        job_manager: JobManagerService,
    ) -> None:
        self._persona_master_repository = persona_master_repository
        self._persona_repository = persona_repository
        self._enriquecimiento_foro_service = enriquecimiento_foro_service
        self._job_manager = job_manager

    def ejecutar(
        self, personas_master: list[PersonaMaster] | None = None, limite: int = 500
    ) -> list[ResultadoEnriquecimientoForoDTO]:
        candidatas = (
            personas_master if personas_master is not None else self._persona_master_repository.listar_activas(limite)
        )

        job = self._job_manager.crear_job(TipoJob.CONSULTA_MASIVA)
        job = self._job_manager.transicionar(job, JobStatus.EN_COLA)
        job = self._job_manager.transicionar(job, JobStatus.CONSULTANDO_FORO)

        resultados: list[ResultadoEnriquecimientoForoDTO] = []
        hubo_error = False
        for persona_master in candidatas:
            try:
                persona = self._persona_repository.buscar_por_id(persona_master.persona_id)
                if persona is None:
                    raise GovDataError(
                        f"Persona de origen no encontrada (persona_id={persona_master.persona_id})"
                    )
                resultado = self._enriquecimiento_foro_service.enriquecer(persona_master, persona, job_id=str(job.id))
                resultados.append(resultado)
            except GovDataError as exc:
                hubo_error = True
                logger.warning(
                    "consulta_foro_masiva_item_fallo", persona_master_id=persona_master.id, error=str(exc)
                )
                continue

        if hubo_error:
            self._job_manager.marcar_error(job, "Uno o mas items fallaron durante la consulta masiva al Foro")
        else:
            job = self._job_manager.transicionar(job, JobStatus.GUARDANDO)  # "FUSIONANDO" (8.14)
            self._job_manager.finalizar(job)

        logger.info("consulta_foro_masiva_completada", cantidad_procesadas=len(resultados))
        return resultados
