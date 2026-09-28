"""Tests: AuditoriaConsultaFuenteService (Submodulo 6.10)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from govdata.application.services.auditoria_consulta_fuente_service import (
    AuditoriaConsultaFuenteService,
)
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from tests.unit.application.fakes_modulo6 import FakeConsultaFuenteLogRepository

_T0 = datetime(2026, 1, 1, tzinfo=UTC)
_T1 = _T0 + timedelta(seconds=3)


class TestAuditoriaConsultaFuenteService:
    def test_iniciar_registra_log_en_progreso(self) -> None:
        repo = FakeConsultaFuenteLogRepository()
        servicio = AuditoriaConsultaFuenteService(repo, ahora_provider=lambda: _T0)
        log = servicio.iniciar(1, FuenteExterna.SENESCYT)
        assert log.iniciado_en == _T0
        assert log.exito is None
        assert log in repo.guardados

    def test_finalizar_calcula_duracion(self) -> None:
        repo = FakeConsultaFuenteLogRepository()
        tiempos = iter([_T0, _T1])
        servicio = AuditoriaConsultaFuenteService(repo, ahora_provider=lambda: next(tiempos))
        log = servicio.iniciar(1, FuenteExterna.SENESCYT)
        finalizado = servicio.finalizar(log, exito=True)
        assert finalizado.duracion_segundos == 3.0
        assert finalizado.exito is True

    def test_finalizar_con_error(self) -> None:
        repo = FakeConsultaFuenteLogRepository()
        servicio = AuditoriaConsultaFuenteService(repo, ahora_provider=lambda: _T0)
        log = servicio.iniciar(1, FuenteExterna.SENESCYT)
        finalizado = servicio.finalizar(log, exito=False, error="timeout")
        assert finalizado.error == "timeout"

    def test_registrar_reintento_incrementa_contador(self) -> None:
        repo = FakeConsultaFuenteLogRepository()
        servicio = AuditoriaConsultaFuenteService(repo, ahora_provider=lambda: _T0)
        log = servicio.iniciar(1, FuenteExterna.SENESCYT)
        servicio.registrar_reintento(log)
        servicio.registrar_reintento(log)
        assert log.reintentos == 2
