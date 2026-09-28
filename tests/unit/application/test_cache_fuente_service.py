"""Tests: CacheFuenteService (Submodulo 6.8)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from govdata.application.services.cache_fuente_service import CacheFuenteService
from govdata.domain.entities.consulta_fuente_log import ConsultaFuenteLog
from govdata.domain.rules.reglas_identidad import ReglasCachePorFuente
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from tests.unit.application.fakes_modulo6 import FakeConsultaFuenteLogRepository

_REGLAS = ReglasCachePorFuente(
    dias_por_fuente={"senescyt": 30, "funcion_judicial": 0}, dias_defecto=7
)
_AHORA = datetime(2026, 6, 1, tzinfo=UTC)


class TestDebeConsultar:
    def test_sin_consultas_previas_siempre_debe_consultar(self) -> None:
        servicio = CacheFuenteService(FakeConsultaFuenteLogRepository(), _REGLAS)
        assert servicio.debe_consultar(1, FuenteExterna.SENESCYT, _AHORA) is True

    def test_ultima_consulta_exitosa_dentro_de_vigencia_no_debe_consultar(self) -> None:
        repo = FakeConsultaFuenteLogRepository()
        log = ConsultaFuenteLog(persona_master_id=1, fuente=FuenteExterna.SENESCYT, iniciado_en=_AHORA - timedelta(days=5))
        log.finalizar(exito=True, cuando=_AHORA - timedelta(days=5), duracion_segundos=1.0)
        repo.guardar(log)

        servicio = CacheFuenteService(repo, _REGLAS)
        assert servicio.debe_consultar(1, FuenteExterna.SENESCYT, _AHORA) is False

    def test_ultima_consulta_exitosa_fuera_de_vigencia_debe_consultar(self) -> None:
        repo = FakeConsultaFuenteLogRepository()
        log = ConsultaFuenteLog(persona_master_id=1, fuente=FuenteExterna.SENESCYT, iniciado_en=_AHORA - timedelta(days=40))
        log.finalizar(exito=True, cuando=_AHORA - timedelta(days=40), duracion_segundos=1.0)
        repo.guardar(log)

        servicio = CacheFuenteService(repo, _REGLAS)
        assert servicio.debe_consultar(1, FuenteExterna.SENESCYT, _AHORA) is True

    def test_ultima_consulta_fallida_nunca_bloquea_reintento(self) -> None:
        repo = FakeConsultaFuenteLogRepository()
        log = ConsultaFuenteLog(persona_master_id=1, fuente=FuenteExterna.SENESCYT, iniciado_en=_AHORA)
        log.finalizar(exito=False, cuando=_AHORA, duracion_segundos=1.0, error="timeout")
        repo.guardar(log)

        servicio = CacheFuenteService(repo, _REGLAS)
        assert servicio.debe_consultar(1, FuenteExterna.SENESCYT, _AHORA) is True

    def test_fuente_sin_configuracion_usa_dias_por_defecto(self) -> None:
        repo = FakeConsultaFuenteLogRepository()
        log = ConsultaFuenteLog(persona_master_id=1, fuente=FuenteExterna.CONTRALORIA, iniciado_en=_AHORA - timedelta(days=3))
        log.finalizar(exito=True, cuando=_AHORA - timedelta(days=3), duracion_segundos=1.0)
        repo.guardar(log)

        servicio = CacheFuenteService(repo, _REGLAS)
        assert servicio.debe_consultar(1, FuenteExterna.CONTRALORIA, _AHORA) is False  # dentro de 7 dias

    def test_fuente_con_vigencia_cero_siempre_vuelve_a_consultar(self) -> None:
        """Ej. Funcion Judicial (24 horas configuradas como 0/1 dia
        cuando ya paso una fraccion de dia)."""
        repo = FakeConsultaFuenteLogRepository()
        log = ConsultaFuenteLog(persona_master_id=1, fuente=FuenteExterna.FUNCION_JUDICIAL, iniciado_en=_AHORA)
        log.finalizar(exito=True, cuando=_AHORA, duracion_segundos=1.0)
        repo.guardar(log)

        servicio = CacheFuenteService(repo, _REGLAS)
        assert servicio.debe_consultar(1, FuenteExterna.FUNCION_JUDICIAL, _AHORA) is True
