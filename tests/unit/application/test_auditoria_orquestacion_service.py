"""Tests: AuditoriaOrquestacionService -- Submodulos 9.10/9.15."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.services.auditoria_orquestacion_service import AuditoriaOrquestacionService
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline
from tests.unit.application.fakes_modulo9 import FakeAuditoriaEtapaRepository

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestAuditoriaOrquestacionService:
    def test_registrar_ejecutado(self) -> None:
        repo = FakeAuditoriaEtapaRepository()
        servicio = AuditoriaOrquestacionService(repo)
        etapa = servicio.registrar_ejecutado("job-1", TipoPasoPipeline.SENESCYT, _AHORA, _AHORA, cantidad_registros=3)
        assert etapa.estado_paso.value == "ejecutado"
        assert etapa.cantidad_registros == 3

    def test_registrar_omitido(self) -> None:
        repo = FakeAuditoriaEtapaRepository()
        servicio = AuditoriaOrquestacionService(repo)
        etapa = servicio.registrar_omitido("job-1", TipoPasoPipeline.FORO, "cache_vigente", _AHORA)
        assert etapa.estado_paso.value == "omitido"
        assert etapa.razon_omision == "cache_vigente"

    def test_registrar_fallido(self) -> None:
        repo = FakeAuditoriaEtapaRepository()
        servicio = AuditoriaOrquestacionService(repo)
        etapa = servicio.registrar_fallido("job-1", TipoPasoPipeline.PERFIL, "timeout", _AHORA, _AHORA)
        assert etapa.estado_paso.value == "fallido"
        assert etapa.error == "timeout"

    def test_listar_por_trabajo(self) -> None:
        repo = FakeAuditoriaEtapaRepository()
        servicio = AuditoriaOrquestacionService(repo)
        servicio.registrar_ejecutado("job-1", TipoPasoPipeline.SENESCYT, _AHORA, _AHORA)
        servicio.registrar_ejecutado("job-2", TipoPasoPipeline.FORO, _AHORA, _AHORA)
        assert len(servicio.listar_por_trabajo("job-1")) == 1
