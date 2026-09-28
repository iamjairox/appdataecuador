"""Tests: ConsultaForoService -- Submodulo 8.17."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.services.consulta_foro_service import ConsultaForoService
from tests.unit.application.fakes_modulo8 import FakeConsultaForoRepository

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestConsultaForoService:
    def test_iniciar_y_finalizar_exito(self) -> None:
        repo = FakeConsultaForoRepository()
        servicio = ConsultaForoService(repo, ahora_provider=lambda: _AHORA)
        consulta = servicio.iniciar(1, job_id="job-1")
        assert consulta.job_id == "job-1"
        finalizada = servicio.finalizar(consulta, exito=True, codigo_http=200)
        assert finalizada.exito is True
        assert finalizada.codigo_http == 200

    def test_finalizar_con_captcha_detectado(self) -> None:
        repo = FakeConsultaForoRepository()
        servicio = ConsultaForoService(repo, ahora_provider=lambda: _AHORA)
        consulta = servicio.iniciar(1)
        finalizada = servicio.finalizar(consulta, exito=False, error="CAPTCHA", captcha_detectado=True)
        assert finalizada.captcha_detectado is True

    def test_ultima_consulta(self) -> None:
        repo = FakeConsultaForoRepository()
        servicio = ConsultaForoService(repo, ahora_provider=lambda: _AHORA)
        servicio.iniciar(1)
        assert servicio.ultima_consulta(1) is not None
        assert servicio.ultima_consulta(2) is None
