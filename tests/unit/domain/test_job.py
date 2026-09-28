"""Tests: entidades Job / JobStep (Submodulo 4.8)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from govdata.domain.entities.job import Job, JobInvalidoError, JobStatus, TipoJob
from govdata.domain.entities.job_step import JobStep, JobStepInvalidoError


class TestJob:
    def test_estado_inicial(self) -> None:
        job = Job(tipo=TipoJob.CONSULTA_INDIVIDUAL)
        assert job.estado == JobStatus.PENDIENTE
        assert job.porcentaje == 0.0

    def test_transicionar_usa_porcentaje_por_defecto(self) -> None:
        job = Job(tipo=TipoJob.CONSULTA_INDIVIDUAL)
        job.transicionar(JobStatus.DESCARGANDO)
        assert job.estado == JobStatus.DESCARGANDO
        assert job.porcentaje == 30.0

    def test_transicionar_con_porcentaje_explicito(self) -> None:
        job = Job(tipo=TipoJob.CONSULTA_INDIVIDUAL)
        job.transicionar(JobStatus.EXTRAYENDO, porcentaje=55.5)
        assert job.porcentaje == 55.5

    def test_finalizar(self) -> None:
        job = Job(tipo=TipoJob.CONSULTA_MASIVA, fecha_inicio=datetime(2026, 1, 1, tzinfo=UTC))
        fin = datetime(2026, 1, 1, 0, 0, 10, tzinfo=UTC)
        job.finalizar(fin)
        assert job.estado == JobStatus.FINALIZADO
        assert job.porcentaje == 100.0
        assert job.duracion_segundos == 10.0

    def test_marcar_error_acumula_mensajes(self) -> None:
        job = Job(tipo=TipoJob.CONSULTA_INDIVIDUAL)
        job.marcar_error("fallo 1", datetime.now(UTC))
        job.errores.append("fallo 2")  # simulando un segundo error acumulado
        assert job.estado == JobStatus.ERROR
        assert len(job.errores) == 2

    def test_registrar_reintento(self) -> None:
        job = Job(tipo=TipoJob.CONSULTA_INDIVIDUAL)
        job.registrar_reintento()
        job.registrar_reintento()
        assert job.reintentos == 2

    def test_porcentaje_fuera_de_rango_invalido(self) -> None:
        with pytest.raises(JobInvalidoError):
            Job(tipo=TipoJob.CONSULTA_INDIVIDUAL, porcentaje=150.0)

    def test_reintentos_negativo_invalido(self) -> None:
        with pytest.raises(JobInvalidoError):
            Job(tipo=TipoJob.CONSULTA_INDIVIDUAL, reintentos=-1)

    def test_duracion_none_sin_fechas(self) -> None:
        job = Job(tipo=TipoJob.CONSULTA_INDIVIDUAL)
        assert job.duracion_segundos is None


class TestJobStep:
    def test_valido(self) -> None:
        import uuid

        step = JobStep(
            job_id=uuid.uuid4(),
            estado=JobStatus.DESCUBRIENDO,
            iniciado_en=datetime(2026, 1, 1, tzinfo=UTC),
            finalizado_en=datetime(2026, 1, 1, 0, 0, 5, tzinfo=UTC),
        )
        assert step.duracion_segundos == 5.0

    def test_finalizado_antes_de_iniciado_invalido(self) -> None:
        import uuid

        with pytest.raises(JobStepInvalidoError):
            JobStep(
                job_id=uuid.uuid4(),
                estado=JobStatus.DESCUBRIENDO,
                iniciado_en=datetime(2026, 1, 1, 0, 0, 5, tzinfo=UTC),
                finalizado_en=datetime(2026, 1, 1, tzinfo=UTC),
            )
