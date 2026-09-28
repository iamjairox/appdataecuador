"""Tests: MotorEstadisticasService (9.12) + DashboardInternoService (9.11)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from govdata.application.services.dashboard_interno_service import DashboardInternoService
from govdata.application.services.motor_estadisticas_service import MotorEstadisticasService
from govdata.domain.value_objects.estado_paso import EstadoPaso
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador
from tests.unit.application.fakes_modulo9 import (
    FakeAuditoriaEtapaRepository,
    FakeTrabajoOrquestadorRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestMotorEstadisticasService:
    def test_calcula_estadisticas_desde_auditoria(self) -> None:
        from govdata.domain.entities.auditoria_etapa import AuditoriaEtapa

        repo = FakeAuditoriaEtapaRepository()
        repo.guardar_lote(
            [
                AuditoriaEtapa(
                    trabajo_orquestador_id="job-1", tipo_paso=TipoPasoPipeline.SENESCYT,
                    estado_paso=EstadoPaso.EJECUTADO, iniciado_en=_AHORA, finalizado_en=_AHORA,
                    cache_utilizada=False,
                ),
                AuditoriaEtapa(
                    trabajo_orquestador_id="job-1", tipo_paso=TipoPasoPipeline.FORO,
                    estado_paso=EstadoPaso.OMITIDO, iniciado_en=_AHORA, razon_omision="cache_vigente",
                    cache_utilizada=True,
                ),
                AuditoriaEtapa(
                    trabajo_orquestador_id="job-1", tipo_paso=TipoPasoPipeline.EXTRACCION,
                    estado_paso=EstadoPaso.EJECUTADO, iniciado_en=_AHORA, finalizado_en=_AHORA,
                    cantidad_registros=10,
                ),
                AuditoriaEtapa(
                    trabajo_orquestador_id="job-1", tipo_paso=TipoPasoPipeline.PERFIL,
                    estado_paso=EstadoPaso.FALLIDO, iniciado_en=_AHORA, finalizado_en=_AHORA, error="x",
                ),
            ]
        )
        servicio = MotorEstadisticasService(repo)
        estadisticas = servicio.calcular()
        assert estadisticas.funcionarios_encontrados == 10
        assert estadisticas.consultas_senescyt == 1
        assert estadisticas.errores == 1
        assert estadisticas.cache_hit == 1  # FORO se omitio por cache_vigente
        assert estadisticas.cache_miss == 1  # SENESCYT se ejecuto de verdad

    def test_sin_datos_retorna_todo_cero(self) -> None:
        servicio = MotorEstadisticasService(FakeAuditoriaEtapaRepository())
        estadisticas = servicio.calcular()
        assert estadisticas.errores == 0
        assert estadisticas.consultas_senescyt == 0


class TestDashboardInternoService:
    def test_construye_dashboard_con_conteos(self) -> None:
        from govdata.domain.entities.trabajo_orquestador import TrabajoOrquestador

        repo = FakeTrabajoOrquestadorRepository()
        t1 = TrabajoOrquestador(tipo=TipoTrabajoOrquestador.CONSULTA_ENTIDAD)
        t1.encolar()
        repo.guardar(t1)

        t2 = TrabajoOrquestador(tipo=TipoTrabajoOrquestador.CONSULTA_ENTIDAD)
        t2.encolar()
        t2.tomar(_AHORA)
        t2.completar(_AHORA + timedelta(seconds=5))
        repo.guardar(t2)

        t3 = TrabajoOrquestador(tipo=TipoTrabajoOrquestador.CONSULTA_ENTIDAD)
        t3.encolar()
        t3.tomar(_AHORA)
        t3.marcar_error("timeout", _AHORA)
        repo.guardar(t3)

        servicio = DashboardInternoService(repo)
        dashboard = servicio.construir()

        assert dashboard.trabajos_pendientes == 1
        assert dashboard.trabajos_completados == 1
        assert dashboard.errores == 1
        assert dashboard.tiempo_promedio_segundos == 5.0
        assert dashboard.ultima_actualizacion is not None

    def test_dashboard_vacio(self) -> None:
        servicio = DashboardInternoService(FakeTrabajoOrquestadorRepository())
        dashboard = servicio.construir()
        assert dashboard.trabajos_activos == 0
        assert dashboard.tiempo_promedio_segundos == 0.0
        assert dashboard.ultima_actualizacion is None
