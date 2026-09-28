"""Caso de uso: EnriquecerMasivoAcademicoUseCase -- Submodulo 7.12
(Consulta Masiva).

    Todas las personas -> Cola -> Consultar -> Actualizar -> Continuar

Opera directamente sobre `PersonaMaster` ya resueltas (Modulo 6,
`PersonaMasterRepositoryPort.listar_activas`, REUTILIZADO) -- a
diferencia de la consulta individual (7.11), NO vuelve a pasar por
`ResolverOCrearPersonaMasterUseCase` por cada item (ya existen, seria
trabajo redundante). Un item que falla NUNCA detiene a los demas -- mismo
principio que `MonitoreoContinuoService.monitorear_masiva` (Modulo 5).
"""

from __future__ import annotations

from govdata.application.dto.resultado_enriquecimiento_academico_dto import (
    ResultadoEnriquecimientoAcademicoDTO,
)
from govdata.application.ports.persona_master_repository_port import PersonaMasterRepositoryPort
from govdata.application.services.enriquecimiento_academico_service import (
    EnriquecimientoAcademicoService,
)
from govdata.application.services.identity_resolution_service import senales_desde_persona_master
from govdata.application.services.job_manager_service import JobManagerService
from govdata.config.logging_config import get_logger
from govdata.domain.entities.job import JobStatus, TipoJob
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import GovDataError

logger = get_logger(__name__)


class EnriquecerMasivoAcademicoUseCase:
    def __init__(
        self,
        persona_master_repository: PersonaMasterRepositoryPort,
        enriquecimiento_service: EnriquecimientoAcademicoService,
        job_manager: JobManagerService,
    ) -> None:
        self._persona_master_repository = persona_master_repository
        self._enriquecimiento_service = enriquecimiento_service
        self._job_manager = job_manager

    def ejecutar(
        self, personas_master: list[PersonaMaster] | None = None, limite: int = 500
    ) -> list[ResultadoEnriquecimientoAcademicoDTO]:
        candidatas = (
            personas_master if personas_master is not None else self._persona_master_repository.listar_activas(limite)
        )

        job = self._job_manager.crear_job(TipoJob.CONSULTA_MASIVA)
        job = self._job_manager.transicionar(job, JobStatus.EN_COLA)

        resultados: list[ResultadoEnriquecimientoAcademicoDTO] = []
        hubo_error = False
        for persona_master in candidatas:
            try:
                senales = senales_desde_persona_master(persona_master)
                resultado = self._enriquecimiento_service.enriquecer(persona_master, senales)
                resultados.append(resultado)
            except GovDataError as exc:
                hubo_error = True
                logger.warning(
                    "enriquecimiento_academico_masivo_item_fallo",
                    persona_master_id=persona_master.id, error=str(exc),
                )
                continue

        if hubo_error:
            self._job_manager.marcar_error(job, "Uno o mas items fallaron durante la consulta masiva")
        else:
            job = self._job_manager.transicionar(job, JobStatus.GUARDANDO)
            self._job_manager.finalizar(job)

        logger.info("enriquecimiento_academico_masivo_completado", cantidad_procesadas=len(resultados))
        return resultados
