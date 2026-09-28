"""Tests: EventoPerfilService (Submodulo 6.12)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from govdata.application.services.evento_perfil_service import EventoPerfilService
from govdata.domain.entities.evento_perfil import EventoPerfil
from govdata.domain.exceptions.domain_exceptions import EventoPerfilInvalidoError
from govdata.domain.value_objects.tipo_evento_identidad import TipoEventoIdentidad
from tests.unit.application.fakes_modulo6 import FakeEventoPerfilRepository

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestEventoPerfilService:
    def test_guardar_lote_vacio_no_llama_al_repositorio(self) -> None:
        repo = FakeEventoPerfilRepository()
        servicio = EventoPerfilService(repo)
        assert servicio.guardar_lote([]) == []
        assert repo.guardados == []

    def test_guardar_lote_persiste_todos(self) -> None:
        repo = FakeEventoPerfilRepository()
        servicio = EventoPerfilService(repo)
        eventos = [
            EventoPerfil(tipo=TipoEventoIdentidad.NUEVA_FUENTE, persona_master_id=1, payload={}, creado_en=_AHORA)
        ]
        assert len(servicio.guardar_lote(eventos)) == 1

    def test_consumir_evento_inexistente_falla(self) -> None:
        servicio = EventoPerfilService(FakeEventoPerfilRepository())
        import uuid

        with pytest.raises(EventoPerfilInvalidoError):
            servicio.consumir(uuid.uuid4(), _AHORA)

    def test_procesar_evento_inexistente_falla(self) -> None:
        servicio = EventoPerfilService(FakeEventoPerfilRepository())
        import uuid

        with pytest.raises(EventoPerfilInvalidoError):
            servicio.procesar(uuid.uuid4(), _AHORA)

    def test_consumir_y_procesar_ciclo_completo(self) -> None:
        repo = FakeEventoPerfilRepository()
        servicio = EventoPerfilService(repo)
        evento = repo.guardar(
            EventoPerfil(tipo=TipoEventoIdentidad.NUEVA_FUENTE, persona_master_id=1, payload={}, creado_en=_AHORA)
        )
        servicio.consumir(evento.id, _AHORA)
        procesado = servicio.procesar(evento.id, _AHORA)
        assert procesado.procesado_en == _AHORA

    def test_listar_pendientes(self) -> None:
        repo = FakeEventoPerfilRepository()
        servicio = EventoPerfilService(repo)
        repo.guardar(
            EventoPerfil(tipo=TipoEventoIdentidad.NUEVA_FUENTE, persona_master_id=1, payload={}, creado_en=_AHORA)
        )
        assert len(servicio.listar_pendientes()) == 1
