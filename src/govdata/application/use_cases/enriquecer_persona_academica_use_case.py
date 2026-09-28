"""Caso de uso: EnriquecerPersonaAcademicaUseCase -- Submodulo 7.11
(Consulta Bajo Demanda).

    Buscar persona -> Existe Perfil Maestro -> ¿Cache vigente? -> Si:
    Mostrar / No: Consultar SENESCYT -> Actualizar -> Mostrar

"Resolver Persona Master" (Modulo 6, `ResolverOCrearPersonaMasterUseCase`,
REUTILIZADO sin modificar) sucede aqui; el resto de la tuberia (cache,
consulta, normalizacion, comparacion, versionado, alertas, eventos) vive
en `EnriquecimientoAcademicoService`. El Job Manager (Modulo 4,
REUTILIZADO) envuelve la corrida completa -- los estados
COMPARANDO/ACTUALIZANDO del Submodulo 7.13 se mapean al `GUARDANDO`
ya existente en `JobStatus` (Modulo 4, congelado, no admite miembros
nuevos): son fases internas de la MISMA transicion de persistencia desde
la perspectiva del Job.
"""

from __future__ import annotations

from govdata.application.dto.resultado_enriquecimiento_academico_dto import (
    ResultadoEnriquecimientoAcademicoDTO,
)
from govdata.application.services.enriquecimiento_academico_service import (
    EnriquecimientoAcademicoService,
)
from govdata.application.services.identity_resolution_service import senales_desde_persona_master
from govdata.application.services.job_manager_service import JobManagerService
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.domain.entities.job import JobStatus, TipoJob
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import GovDataError


class EnriquecerPersonaAcademicaUseCase:
    def __init__(
        self,
        resolver_persona_master_use_case: ResolverOCrearPersonaMasterUseCase,
        enriquecimiento_service: EnriquecimientoAcademicoService,
        job_manager: JobManagerService,
    ) -> None:
        self._resolver_persona_master_use_case = resolver_persona_master_use_case
        self._enriquecimiento_service = enriquecimiento_service
        self._job_manager = job_manager

    def ejecutar(
        self, persona: Persona, cargo: str | None = None, institucion: str | None = None
    ) -> ResultadoEnriquecimientoAcademicoDTO:
        job = self._job_manager.crear_job(TipoJob.CONSULTA_INDIVIDUAL)
        job = self._job_manager.transicionar(job, JobStatus.EN_COLA)
        try:
            persona_master = self._resolver_persona_master_use_case.ejecutar(persona, cargo=cargo, institucion=institucion)

            job = self._job_manager.transicionar(job, JobStatus.CONSULTANDO_SENESCYT)
            senales = senales_desde_persona_master(persona_master, cargo=cargo, institucion=institucion)
            job = self._job_manager.transicionar(job, JobStatus.NORMALIZANDO)
            resultado = self._enriquecimiento_service.enriquecer(persona_master, senales)

            if resultado.error is not None:
                self._job_manager.marcar_error(job, resultado.error)
            else:
                job = self._job_manager.transicionar(job, JobStatus.GUARDANDO)
                self._job_manager.finalizar(job)
            return resultado
        except GovDataError as exc:
            self._job_manager.marcar_error(job, str(exc))
            raise
