"""Tests: AlertaPerfilService (Submodulo 6.13)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.services.alerta_perfil_service import AlertaPerfilService
from govdata.domain.entities.alerta_perfil import AlertaPerfil
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_perfil import TipoAlertaPerfil
from tests.unit.application.fakes_modulo6 import FakeAlertaPerfilRepository

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestAlertaPerfilService:
    def test_guardar_lote_vacio(self) -> None:
        servicio = AlertaPerfilService(FakeAlertaPerfilRepository())
        assert servicio.guardar_lote([]) == []

    def test_guardar_lote_y_listar_por_persona_master(self) -> None:
        repo = FakeAlertaPerfilRepository()
        servicio = AlertaPerfilService(repo)
        alerta = AlertaPerfil(
            persona_master_id=1, tipo=TipoAlertaPerfil.TITULO_CAMBIADO, prioridad=NivelCriticidad.MEDIO,
            descripcion="x", detectado_en=_AHORA,
        )
        servicio.guardar_lote([alerta])
        assert len(servicio.listar_por_persona_master(1)) == 1
