"""Tests: CacheSenescytService (Submodulo 7.10)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from govdata.application.services.cache_senescyt_service import CacheSenescytService
from govdata.domain.entities.consulta_senescyt import ConsultaSenescyt
from govdata.domain.rules.reglas_academicas import ReglasCacheSenescyt
from tests.unit.application.fakes_modulo7 import FakeConsultaSenescytRepository

_REGLAS = ReglasCacheSenescyt(dias_vigencia=30)
_AHORA = datetime(2026, 6, 1, tzinfo=UTC)


class TestDebeConsultar:
    def test_sin_consultas_previas_siempre_debe_consultar(self) -> None:
        servicio = CacheSenescytService(FakeConsultaSenescytRepository(), _REGLAS)
        assert servicio.debe_consultar(1, _AHORA) is True

    def test_consulta_exitosa_dentro_de_vigencia_no_debe_consultar(self) -> None:
        repo = FakeConsultaSenescytRepository()
        consulta = ConsultaSenescyt(persona_master_id=1, iniciado_en=_AHORA - timedelta(days=10))
        consulta.finalizar(exito=True, cuando=_AHORA - timedelta(days=10), duracion_segundos=1.0)
        repo.guardar(consulta)
        servicio = CacheSenescytService(repo, _REGLAS)
        assert servicio.debe_consultar(1, _AHORA) is False

    def test_consulta_exitosa_fuera_de_vigencia_debe_consultar(self) -> None:
        repo = FakeConsultaSenescytRepository()
        consulta = ConsultaSenescyt(persona_master_id=1, iniciado_en=_AHORA - timedelta(days=40))
        consulta.finalizar(exito=True, cuando=_AHORA - timedelta(days=40), duracion_segundos=1.0)
        repo.guardar(consulta)
        servicio = CacheSenescytService(repo, _REGLAS)
        assert servicio.debe_consultar(1, _AHORA) is True

    def test_consulta_fallida_nunca_bloquea_reintento(self) -> None:
        repo = FakeConsultaSenescytRepository()
        consulta = ConsultaSenescyt(persona_master_id=1, iniciado_en=_AHORA)
        consulta.finalizar(exito=False, cuando=_AHORA, duracion_segundos=1.0, error="timeout")
        repo.guardar(consulta)
        servicio = CacheSenescytService(repo, _REGLAS)
        assert servicio.debe_consultar(1, _AHORA) is True
