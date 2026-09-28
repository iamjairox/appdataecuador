"""Tests: EventoAcademicoService (Submodulo 7.9)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from govdata.application.services.evento_academico_service import EventoAcademicoService
from govdata.domain.entities.evento_academico import EventoAcademico
from govdata.domain.exceptions.domain_exceptions import EventoAcademicoInvalidoError
from govdata.domain.value_objects.tipo_evento_academico import TipoEventoAcademico
from tests.unit.application.fakes_modulo7 import FakeEventoAcademicoRepository

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestEventoAcademicoService:
    def test_guardar_lote_vacio(self) -> None:
        servicio = EventoAcademicoService(FakeEventoAcademicoRepository())
        assert servicio.guardar_lote([]) == []

    def test_consumir_evento_inexistente_falla(self) -> None:
        servicio = EventoAcademicoService(FakeEventoAcademicoRepository())
        with pytest.raises(EventoAcademicoInvalidoError):
            servicio.consumir(uuid.uuid4(), _AHORA)

    def test_procesar_evento_inexistente_falla(self) -> None:
        servicio = EventoAcademicoService(FakeEventoAcademicoRepository())
        with pytest.raises(EventoAcademicoInvalidoError):
            servicio.procesar(uuid.uuid4(), _AHORA)

    def test_consumir_y_procesar_ciclo_completo(self) -> None:
        repo = FakeEventoAcademicoRepository()
        servicio = EventoAcademicoService(repo)
        evento = repo.guardar(
            EventoAcademico(tipo=TipoEventoAcademico.TITULO_NUEVO, persona_master_id=1, payload={}, creado_en=_AHORA)
        )
        servicio.consumir(evento.id, _AHORA)
        procesado = servicio.procesar(evento.id, _AHORA)
        assert procesado.procesado_en == _AHORA

    def test_listar_pendientes(self) -> None:
        repo = FakeEventoAcademicoRepository()
        servicio = EventoAcademicoService(repo)
        repo.guardar(
            EventoAcademico(tipo=TipoEventoAcademico.TITULO_NUEVO, persona_master_id=1, payload={}, creado_en=_AHORA)
        )
        assert len(servicio.listar_pendientes()) == 1
