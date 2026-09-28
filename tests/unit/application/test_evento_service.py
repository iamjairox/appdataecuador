"""Tests: EventoService (Submodulo 5.7)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from govdata.application.services.evento_service import EventoService
from govdata.domain.entities.alerta import Alerta, TipoAlerta
from govdata.domain.entities.evento import EstadoEvento, TipoEvento
from govdata.domain.entities.oportunidad_comercial import OportunidadComercial, TipoOportunidad
from govdata.domain.exceptions.domain_exceptions import EventoInvalidoError
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from tests.unit.application.fakes_modulo5 import FakeEventoRepository


def _alerta() -> Alerta:
    return Alerta(
        entidad_id=1, tipo=TipoAlerta.CAMBIO_CORREO, prioridad=NivelCriticidad.MEDIO,
        descripcion="x", detectado_en=datetime.now(UTC),
    )


def _oportunidad() -> OportunidadComercial:
    return OportunidadComercial(
        entidad_id=1, tipo=TipoOportunidad.NUEVO_PROCURADOR, descripcion="x", detectado_en=datetime.now(UTC)
    )


class TestCrearEventos:
    def test_crear_desde_alertas(self) -> None:
        repo = FakeEventoRepository()
        servicio = EventoService(repo)
        eventos = servicio.crear_desde_alertas([_alerta()], datetime.now(UTC))
        assert len(eventos) == 1
        assert eventos[0].tipo == TipoEvento.ALERTA
        assert eventos[0].estado == EstadoEvento.PENDIENTE

    def test_crear_desde_oportunidades(self) -> None:
        repo = FakeEventoRepository()
        servicio = EventoService(repo)
        eventos = servicio.crear_desde_oportunidades([_oportunidad()], datetime.now(UTC))
        assert len(eventos) == 1
        assert eventos[0].tipo == TipoEvento.OPORTUNIDAD_COMERCIAL

    def test_lista_vacia_no_crea_nada(self) -> None:
        repo = FakeEventoRepository()
        servicio = EventoService(repo)
        assert servicio.crear_desde_alertas([], datetime.now(UTC)) == []
        assert repo.guardados == []


class TestTransicionesDeEstado:
    def test_consumir(self) -> None:
        repo = FakeEventoRepository()
        servicio = EventoService(repo)
        (evento,) = servicio.crear_desde_alertas([_alerta()], datetime.now(UTC))
        actualizado = servicio.consumir(evento.id, datetime.now(UTC))
        assert actualizado.estado == EstadoEvento.CONSUMIDO

    def test_procesar_despues_de_consumir(self) -> None:
        repo = FakeEventoRepository()
        servicio = EventoService(repo)
        (evento,) = servicio.crear_desde_alertas([_alerta()], datetime.now(UTC))
        servicio.consumir(evento.id, datetime.now(UTC))
        actualizado = servicio.procesar(evento.id, datetime.now(UTC))
        assert actualizado.estado == EstadoEvento.PROCESADO

    def test_consumir_evento_inexistente_lanza_error(self) -> None:
        repo = FakeEventoRepository()
        servicio = EventoService(repo)
        with pytest.raises(EventoInvalidoError):
            servicio.consumir(uuid.uuid4(), datetime.now(UTC))

    def test_procesar_evento_inexistente_lanza_error(self) -> None:
        repo = FakeEventoRepository()
        servicio = EventoService(repo)
        with pytest.raises(EventoInvalidoError):
            servicio.procesar(uuid.uuid4(), datetime.now(UTC))


class TestListarPendientes:
    def test_lista_solo_pendientes(self) -> None:
        repo = FakeEventoRepository()
        servicio = EventoService(repo)
        eventos = servicio.crear_desde_alertas([_alerta(), _alerta()], datetime.now(UTC))
        servicio.consumir(eventos[0].id, datetime.now(UTC))
        pendientes = servicio.listar_pendientes(limite=10)
        assert len(pendientes) == 1
        assert pendientes[0].id == eventos[1].id
