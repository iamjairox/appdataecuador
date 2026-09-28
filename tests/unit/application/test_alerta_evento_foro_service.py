"""Tests: AlertaForoService + EventoForoService -- Submodulo 8.7."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from govdata.application.services.alerta_foro_service import AlertaForoService
from govdata.application.services.evento_foro_service import EventoForoService
from govdata.domain.entities.alerta_foro import AlertaForo
from govdata.domain.entities.evento_foro import EventoForo
from govdata.domain.exceptions.domain_exceptions import EventoForoInvalidoError
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_foro import TipoAlertaForo
from govdata.domain.value_objects.tipo_evento_foro import TipoEventoForo
from tests.unit.application.fakes_modulo8 import FakeAlertaForoRepository, FakeEventoForoRepository

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestAlertaForoService:
    def test_guardar_lote_vacio_no_llama_al_repositorio(self) -> None:
        servicio = AlertaForoService(FakeAlertaForoRepository())
        assert servicio.guardar_lote([]) == []

    def test_guardar_y_listar_pendientes(self) -> None:
        repo = FakeAlertaForoRepository()
        servicio = AlertaForoService(repo)
        alerta = AlertaForo(
            persona_master_id=1, tipo=TipoAlertaForo.CAMBIO_ESTADO, prioridad=NivelCriticidad.ALTO,
            descripcion="x", detectado_en=_AHORA,
        )
        servicio.guardar_lote([alerta])
        assert len(servicio.listar_por_persona_master(1)) == 1
        assert len(servicio.listar_pendientes()) == 1


class TestEventoForoService:
    def test_consumir_evento_inexistente_lanza_error(self) -> None:
        servicio = EventoForoService(FakeEventoForoRepository())
        with pytest.raises(EventoForoInvalidoError):
            servicio.consumir(uuid.uuid4(), _AHORA)

    def test_guardar_consumir_y_procesar(self) -> None:
        repo = FakeEventoForoRepository()
        servicio = EventoForoService(repo)
        evento = EventoForo(tipo=TipoEventoForo.REGISTRO_NUEVO, persona_master_id=1, payload={}, creado_en=_AHORA)
        servicio.guardar_lote([evento])
        assert len(servicio.listar_pendientes()) == 1
        consumido = servicio.consumir(evento.id, _AHORA)
        assert consumido.consumido_en == _AHORA
        procesado = servicio.procesar(evento.id, _AHORA)
        assert procesado.procesado_en == _AHORA
