"""Tests: CacheForoService -- Submodulo 8.8."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from govdata.application.services.cache_foro_service import CacheForoService
from govdata.domain.entities.consulta_foro import ConsultaForo
from govdata.domain.rules.reglas_foro import ReglasCacheForo
from tests.unit.application.fakes_modulo8 import FakeConsultaForoRepository

_AHORA = datetime(2026, 1, 10, tzinfo=UTC)


class TestCacheForoService:
    def test_sin_consultas_previas_debe_consultar(self) -> None:
        servicio = CacheForoService(FakeConsultaForoRepository(), ReglasCacheForo(dias_vigencia=7))
        assert servicio.debe_consultar(1, _AHORA) is True

    def test_consulta_reciente_exitosa_omite_nueva_consulta(self) -> None:
        repo = FakeConsultaForoRepository()
        consulta = ConsultaForo(persona_master_id=1, iniciado_en=_AHORA - timedelta(days=1))
        consulta.finalizar(exito=True, cuando=_AHORA - timedelta(days=1), duracion_segundos=1.0)
        repo.guardar(consulta)
        servicio = CacheForoService(repo, ReglasCacheForo(dias_vigencia=7))
        assert servicio.debe_consultar(1, _AHORA) is False

    def test_consulta_vencida_requiere_nueva_consulta(self) -> None:
        repo = FakeConsultaForoRepository()
        consulta = ConsultaForo(persona_master_id=1, iniciado_en=_AHORA - timedelta(days=10))
        consulta.finalizar(exito=True, cuando=_AHORA - timedelta(days=10), duracion_segundos=1.0)
        repo.guardar(consulta)
        servicio = CacheForoService(repo, ReglasCacheForo(dias_vigencia=7))
        assert servicio.debe_consultar(1, _AHORA) is True

    def test_ultima_consulta_fallida_requiere_nueva_consulta(self) -> None:
        repo = FakeConsultaForoRepository()
        consulta = ConsultaForo(persona_master_id=1, iniciado_en=_AHORA - timedelta(hours=1))
        consulta.finalizar(exito=False, cuando=_AHORA - timedelta(hours=1), duracion_segundos=1.0, error="timeout")
        repo.guardar(consulta)
        servicio = CacheForoService(repo, ReglasCacheForo(dias_vigencia=7))
        assert servicio.debe_consultar(1, _AHORA) is True
