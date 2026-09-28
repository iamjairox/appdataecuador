"""Tests: MetricasAcademicasService (Submodulo 7.18)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.services.metricas_academicas_service import MetricasAcademicasService
from govdata.domain.entities.consulta_senescyt import ConsultaSenescyt
from govdata.domain.entities.historial_academico import HistorialAcademico
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico
from tests.unit.application.fakes_modulo7 import (
    FakeConsultaSenescytRepository,
    FakeHistorialAcademicoRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestCalcular:
    def test_sin_datos_da_metricas_vacias(self) -> None:
        servicio = MetricasAcademicasService(FakeConsultaSenescytRepository(), FakeHistorialAcademicoRepository())
        metricas = servicio.calcular()
        assert metricas.consultas_exitosas == 0
        assert metricas.tiempo_promedio_segundos == 0.0

    def test_calcula_tiempos_y_contadores(self) -> None:
        consulta_repo = FakeConsultaSenescytRepository()
        historial_repo = FakeHistorialAcademicoRepository()

        c1 = ConsultaSenescyt(persona_master_id=1, iniciado_en=_AHORA)
        c1.finalizar(exito=True, cuando=_AHORA, duracion_segundos=2.0, cache_utilizado=False)
        consulta_repo.guardar(c1)

        c2 = ConsultaSenescyt(persona_master_id=2, iniciado_en=_AHORA)
        c2.finalizar(exito=True, cuando=_AHORA, duracion_segundos=4.0, cache_utilizado=True)
        c2.registrar_reintento()
        consulta_repo.guardar(c2)

        c3 = ConsultaSenescyt(persona_master_id=3, iniciado_en=_AHORA)
        c3.finalizar(exito=False, cuando=_AHORA, duracion_segundos=1.0, error="timeout")
        consulta_repo.guardar(c3)

        historial_repo.guardar_lote(
            [
                HistorialAcademico(
                    persona_master_id=1, clave_titulo="x", tipo_cambio=TipoCambioAcademico.TITULO_NUEVO,
                    detectado_en=_AHORA, consulta_senescyt_id=1,
                ),
                HistorialAcademico(
                    persona_master_id=1, clave_titulo="y", tipo_cambio=TipoCambioAcademico.CAMBIO_NIVEL,
                    detectado_en=_AHORA, consulta_senescyt_id=1,
                ),
            ]
        )

        servicio = MetricasAcademicasService(consulta_repo, historial_repo)
        metricas = servicio.calcular()

        assert metricas.consultas_exitosas == 2
        assert metricas.consultas_fallidas == 1
        assert metricas.cache_hit == 1
        assert metricas.cache_miss == 2
        assert metricas.reintentos == 1
        assert metricas.tiempo_promedio_segundos == round((2.0 + 4.0 + 1.0) / 3, 4)
        assert metricas.tiempo_maximo_segundos == 4.0
        assert metricas.tiempo_minimo_segundos == 1.0
        assert metricas.cambios_detectados == 2
        assert metricas.titulos_nuevos == 1
