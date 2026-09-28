"""Tests: JobManagerService (Submodulo 4.8)."""

from __future__ import annotations

from govdata.application.services.job_manager_service import JobManagerService
from govdata.domain.entities.job import JobStatus, TipoJob
from tests.unit.application.fakes_extraccion import FakeJobRepository


def test_crear_job() -> None:
    repo = FakeJobRepository()
    servicio = JobManagerService(repo)
    job = servicio.crear_job(TipoJob.CONSULTA_INDIVIDUAL, entidad_id=5)

    assert job.estado == JobStatus.PENDIENTE
    assert job.entidad_id == 5
    assert job.fecha_inicio is not None
    assert repo.jobs[job.id] is job


def test_transicionar_registra_step() -> None:
    repo = FakeJobRepository()
    servicio = JobManagerService(repo)
    job = servicio.crear_job(TipoJob.CONSULTA_INDIVIDUAL)

    servicio.transicionar(job, JobStatus.DESCUBRIENDO)

    assert job.estado == JobStatus.DESCUBRIENDO
    steps = repo.listar_steps(job.id)
    assert len(steps) == 1
    assert steps[0].estado == JobStatus.DESCUBRIENDO


def test_finalizar() -> None:
    repo = FakeJobRepository()
    servicio = JobManagerService(repo)
    job = servicio.crear_job(TipoJob.CONSULTA_INDIVIDUAL)
    servicio.finalizar(job)

    assert job.estado == JobStatus.FINALIZADO
    assert job.porcentaje == 100.0
    assert len(repo.listar_steps(job.id)) == 1


def test_marcar_error() -> None:
    repo = FakeJobRepository()
    servicio = JobManagerService(repo)
    job = servicio.crear_job(TipoJob.CONSULTA_INDIVIDUAL)
    servicio.marcar_error(job, "algo fallo")

    assert job.estado == JobStatus.ERROR
    assert "algo fallo" in job.errores
    assert repo.listar_steps(job.id)[0].mensaje == "algo fallo"


def test_registrar_reintento() -> None:
    repo = FakeJobRepository()
    servicio = JobManagerService(repo)
    job = servicio.crear_job(TipoJob.CONSULTA_MASIVA)
    servicio.registrar_reintento(job)
    servicio.registrar_reintento(job)

    assert job.reintentos == 2
