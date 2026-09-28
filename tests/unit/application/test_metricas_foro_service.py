"""Tests: MetricasForoService -- Submodulo 8.15."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.services.metricas_foro_service import MetricasForoService
from govdata.domain.entities.consulta_foro import ConsultaForo
from tests.unit.application.fakes_modulo8 import FakeConsultaForoRepository

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestMetricasForoService:
    def test_sin_consultas_retorna_ceros(self) -> None:
        servicio = MetricasForoService(FakeConsultaForoRepository())
        metricas = servicio.calcular()
        assert metricas.cantidad_consultada == 0
        assert metricas.tiempo_promedio_segundos == 0.0

    def test_calcula_metricas_agregadas(self) -> None:
        repo = FakeConsultaForoRepository()

        exitosa = ConsultaForo(persona_master_id=1, iniciado_en=_AHORA)
        exitosa.finalizar(exito=True, cuando=_AHORA, duracion_segundos=2.0, cache_utilizado=False)
        repo.guardar(exitosa)

        fallida = ConsultaForo(persona_master_id=2, iniciado_en=_AHORA)
        fallida.registrar_reintento()
        fallida.registrar_reintento()
        fallida.finalizar(exito=False, cuando=_AHORA, duracion_segundos=4.0, error="timeout")
        repo.guardar(fallida)

        desde_cache = ConsultaForo(persona_master_id=3, iniciado_en=_AHORA)
        desde_cache.finalizar(exito=True, cuando=_AHORA, duracion_segundos=0.0, cache_utilizado=True)
        repo.guardar(desde_cache)

        metricas = MetricasForoService(repo).calcular()
        assert metricas.cantidad_consultada == 3
        assert metricas.cantidad_exitosa == 2
        assert metricas.cantidad_con_error == 1
        assert metricas.errores == 2
        assert metricas.cache_hit == 1
        assert metricas.cache_miss == 2
        assert metricas.tiempo_promedio_segundos == 2.0
