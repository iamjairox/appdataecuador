"""Tests: ConsultaSenescytService (Submodulo 7.15, auditoria)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from govdata.application.services.consulta_senescyt_service import ConsultaSenescytService
from tests.unit.application.fakes_modulo7 import FakeConsultaSenescytRepository

_T0 = datetime(2026, 1, 1, tzinfo=UTC)
_T1 = _T0 + timedelta(seconds=4)


class TestConsultaSenescytService:
    def test_iniciar_registra_consulta_en_progreso(self) -> None:
        repo = FakeConsultaSenescytRepository()
        servicio = ConsultaSenescytService(repo, ahora_provider=lambda: _T0)
        consulta = servicio.iniciar(1)
        assert consulta.exito is None
        assert consulta in repo.guardadas

    def test_finalizar_calcula_duracion_y_guarda_cache_y_version(self) -> None:
        repo = FakeConsultaSenescytRepository()
        tiempos = iter([_T0, _T1])
        servicio = ConsultaSenescytService(repo, ahora_provider=lambda: next(tiempos))
        consulta = servicio.iniciar(1)
        finalizada = servicio.finalizar(
            consulta, exito=True, version_resultante=3, respuesta_cruda={"a": 1}, cache_utilizado=True
        )
        assert finalizada.duracion_segundos == 4.0
        assert finalizada.version_resultante == 3
        assert finalizada.cache_utilizado is True

    def test_finalizar_con_error(self) -> None:
        repo = FakeConsultaSenescytRepository()
        servicio = ConsultaSenescytService(repo, ahora_provider=lambda: _T0)
        consulta = servicio.iniciar(1)
        finalizada = servicio.finalizar(consulta, exito=False, error="timeout")
        assert finalizada.error == "timeout"

    def test_ultima_consulta(self) -> None:
        repo = FakeConsultaSenescytRepository()
        servicio = ConsultaSenescytService(repo, ahora_provider=lambda: _T0)
        consulta = servicio.iniciar(1)
        assert servicio.ultima_consulta(1) == consulta
