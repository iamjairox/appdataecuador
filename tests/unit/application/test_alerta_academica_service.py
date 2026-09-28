"""Tests: AlertaAcademicaService (Submodulo 7.8)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.services.alerta_academica_service import AlertaAcademicaService
from govdata.domain.entities.alerta_academica import AlertaAcademica
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_academica import TipoAlertaAcademica
from tests.unit.application.fakes_modulo7 import FakeAlertaAcademicaRepository

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestAlertaAcademicaService:
    def test_guardar_lote_vacio(self) -> None:
        servicio = AlertaAcademicaService(FakeAlertaAcademicaRepository())
        assert servicio.guardar_lote([]) == []

    def test_guardar_lote_listar_por_persona_master_y_pendientes(self) -> None:
        repo = FakeAlertaAcademicaRepository()
        servicio = AlertaAcademicaService(repo)
        alerta = AlertaAcademica(
            persona_master_id=1, tipo=TipoAlertaAcademica.NUEVO_TITULO, prioridad=NivelCriticidad.MEDIO,
            descripcion="x", detectado_en=_AHORA,
        )
        servicio.guardar_lote([alerta])
        assert len(servicio.listar_por_persona_master(1)) == 1
        assert len(servicio.listar_pendientes()) == 1
