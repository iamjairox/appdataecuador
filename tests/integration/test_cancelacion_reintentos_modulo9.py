"""Tests de integracion -- cancelacion y reintentos (Submodulos 9.6/9.8)
contra SQLite real: el `intentos`/`max_intentos`/`version_lock` que se
persisten deben sobrevivir un ciclo completo de guardar/recargar, no solo
en el objeto en memoria como en los tests unitarios (`fakes_modulo9.py`)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.services.cola_trabajos_orquestador_service import (
    ColaTrabajosOrquestadorService,
)
from govdata.domain.value_objects.estado_trabajo_orquestador import EstadoTrabajoOrquestador
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_trabajo_orquestador_repository import (
    SqlAlchemyTrabajoOrquestadorRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _cola(sesion) -> ColaTrabajosOrquestadorService:
    return ColaTrabajosOrquestadorService(SqlAlchemyTrabajoOrquestadorRepository(sesion), ahora_provider=lambda: _AHORA)


class TestCancelacion:
    def test_cancelar_trabajo_en_cola_persiste(self, sesion) -> None:
        cola = _cola(sesion)
        trabajo = cola.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": "X"}, "consulta_rapida")

        cola.cancelar(trabajo)
        sesion.flush()

        recargado = cola.buscar_por_id(trabajo.id)
        assert recargado is not None
        assert recargado.estado == EstadoTrabajoOrquestador.CANCELADO

    def test_trabajo_cancelado_no_aparece_en_pendientes(self, sesion) -> None:
        cola = _cola(sesion)
        a_cancelar = cola.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": "X"}, "consulta_rapida")
        cola.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": "Y"}, "consulta_rapida")
        cola.cancelar(a_cancelar)
        sesion.flush()

        siguiente = cola.tomar_siguiente()
        assert siguiente is not None
        assert siguiente.parametros["nombre_entidad"] == "Y"
        assert cola.tomar_siguiente() is None


class TestReintentos:
    def test_reintenta_hasta_agotar_max_intentos_persistiendo_el_contador(self, sesion) -> None:
        cola = _cola(sesion)
        trabajo = cola.encolar(
            TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": "X"}, "masiva_nocturna", max_intentos=2,
        )
        cola.iniciar_directo(trabajo)
        cola.marcar_error(trabajo, "timeout transitorio")
        sesion.flush()

        assert cola.reintentar_si_corresponde(trabajo) is True
        sesion.flush()
        recargado_1 = cola.buscar_por_id(trabajo.id)
        assert recargado_1 is not None
        assert recargado_1.intentos == 1
        assert recargado_1.estado == EstadoTrabajoOrquestador.REINTENTANDO

        cola.iniciar_directo(trabajo)
        cola.marcar_error(trabajo, "timeout transitorio otra vez")
        sesion.flush()

        assert cola.reintentar_si_corresponde(trabajo) is True
        sesion.flush()
        recargado_2 = cola.buscar_por_id(trabajo.id)
        assert recargado_2 is not None
        assert recargado_2.intentos == 2

        # Presupuesto agotado (max_intentos=2): un tercer error ya no se
        # puede reintentar.
        cola.iniciar_directo(trabajo)
        cola.marcar_error(trabajo, "timeout definitivo")
        sesion.flush()
        assert cola.reintentar_si_corresponde(trabajo) is False

        final = cola.buscar_por_id(trabajo.id)
        assert final is not None
        assert final.estado == EstadoTrabajoOrquestador.ERROR
        assert final.intentos == 2

    def test_version_lock_avanza_en_cada_transicion_persistida(self, sesion) -> None:
        cola = _cola(sesion)
        trabajo = cola.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": "X"}, "consulta_rapida")
        version_tras_encolar = trabajo.version_lock

        cola.iniciar_directo(trabajo)
        sesion.flush()
        recargado = cola.buscar_por_id(trabajo.id)
        assert recargado is not None
        assert recargado.version_lock == version_tras_encolar + 1
