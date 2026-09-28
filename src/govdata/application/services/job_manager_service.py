"""Servicio: JobManagerService -- Submodulo 4.8.

Administra el ciclo de vida de un `Job`: crearlo, transicionar su estado
(dejando rastro en `JobStep` en cada transicion), finalizarlo o marcarlo
en error. `ConsultaService` (Submodulos 4.5-4.7) es el unico consumidor
de este servicio -- ningun otro modulo crea Jobs directamente.
"""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.ports.job_repository_port import JobRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.job import Job, JobStatus, TipoJob
from govdata.domain.entities.job_step import JobStep

logger = get_logger(__name__)


class JobManagerService:
    def __init__(self, job_repository: JobRepositoryPort) -> None:
        self._job_repository = job_repository

    def crear_job(self, tipo: TipoJob, entidad_id: int | None = None) -> Job:
        job = Job(tipo=tipo, entidad_id=entidad_id, estado=JobStatus.PENDIENTE, fecha_inicio=datetime.now(UTC))
        job = self._job_repository.guardar(job)
        logger.info("job_creado", job_id=str(job.id), tipo=tipo.value, entidad_id=entidad_id)
        return job

    def transicionar(self, job: Job, nuevo_estado: JobStatus, mensaje: str | None = None) -> Job:
        ahora = datetime.now(UTC)
        job.transicionar(nuevo_estado)
        job = self._job_repository.guardar(job)
        self._job_repository.registrar_step(
            JobStep(job_id=job.id, estado=nuevo_estado, iniciado_en=ahora, finalizado_en=ahora, mensaje=mensaje)
        )
        logger.info("job_transicion", job_id=str(job.id), estado=nuevo_estado.value, porcentaje=job.porcentaje)
        return job

    def finalizar(self, job: Job) -> Job:
        ahora = datetime.now(UTC)
        job.finalizar(ahora)
        job = self._job_repository.guardar(job)
        self._job_repository.registrar_step(
            JobStep(job_id=job.id, estado=JobStatus.FINALIZADO, iniciado_en=ahora, finalizado_en=ahora)
        )
        logger.info("job_finalizado", job_id=str(job.id), duracion_segundos=job.duracion_segundos)
        return job

    def marcar_error(self, job: Job, mensaje: str) -> Job:
        ahora = datetime.now(UTC)
        job.marcar_error(mensaje, ahora)
        job = self._job_repository.guardar(job)
        self._job_repository.registrar_step(
            JobStep(job_id=job.id, estado=JobStatus.ERROR, iniciado_en=ahora, finalizado_en=ahora, mensaje=mensaje)
        )
        logger.error("job_error", job_id=str(job.id), error=mensaje)
        return job

    def registrar_reintento(self, job: Job) -> Job:
        job.registrar_reintento()
        return self._job_repository.guardar(job)
