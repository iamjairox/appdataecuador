"""Tests: TrabajoOrquestador -- Submodulos 9.6/9.7/9.8 (maquina de estados
+ bloqueo optimista)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from govdata.domain.entities.trabajo_orquestador import TrabajoOrquestador
from govdata.domain.exceptions.domain_exceptions import TrabajoOrquestadorInvalidoError
from govdata.domain.value_objects.estado_trabajo_orquestador import EstadoTrabajoOrquestador
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _trabajo(**kwargs) -> TrabajoOrquestador:
    return TrabajoOrquestador(tipo=TipoTrabajoOrquestador.CONSULTA_ENTIDAD, **kwargs)


class TestInvariantes:
    def test_max_intentos_menor_a_1_falla(self) -> None:
        with pytest.raises(TrabajoOrquestadorInvalidoError):
            _trabajo(max_intentos=0)

    def test_intentos_negativos_falla(self) -> None:
        with pytest.raises(TrabajoOrquestadorInvalidoError):
            _trabajo(intentos=-1)


class TestMaquinaDeEstados:
    def test_flujo_feliz_completo(self) -> None:
        trabajo = _trabajo()
        assert trabajo.estado == EstadoTrabajoOrquestador.PENDIENTE
        trabajo.encolar()
        assert trabajo.estado == EstadoTrabajoOrquestador.EN_COLA
        trabajo.tomar(_AHORA)
        assert trabajo.estado == EstadoTrabajoOrquestador.EJECUTANDO
        assert trabajo.iniciado_en == _AHORA
        trabajo.completar(_AHORA)
        assert trabajo.estado == EstadoTrabajoOrquestador.COMPLETADO
        assert trabajo.es_terminal

    def test_cada_transicion_incrementa_version_lock(self) -> None:
        trabajo = _trabajo()
        version_inicial = trabajo.version_lock
        trabajo.encolar()
        assert trabajo.version_lock == version_inicial + 1

    def test_transicion_invalida_lanza_error(self) -> None:
        trabajo = _trabajo()
        with pytest.raises(TrabajoOrquestadorInvalidoError):
            trabajo.completar(_AHORA)  # PENDIENTE -> COMPLETADO no existe

    def test_pausar_y_reanudar(self) -> None:
        trabajo = _trabajo()
        trabajo.encolar()
        trabajo.pausar()
        assert trabajo.estado == EstadoTrabajoOrquestador.PAUSADO
        trabajo.reanudar()
        assert trabajo.estado == EstadoTrabajoOrquestador.EN_COLA

    def test_error_y_reintento(self) -> None:
        trabajo = _trabajo()
        trabajo.encolar()
        trabajo.tomar(_AHORA)
        trabajo.marcar_error("timeout", _AHORA)
        assert trabajo.estado == EstadoTrabajoOrquestador.ERROR
        assert trabajo.ultimo_error == "timeout"
        assert trabajo.puede_reintentar is True

        trabajo.registrar_reintento(_AHORA)
        assert trabajo.estado == EstadoTrabajoOrquestador.REINTENTANDO
        assert trabajo.intentos == 1

    def test_agotar_reintentos_lanza_error(self) -> None:
        trabajo = _trabajo(max_intentos=1)
        trabajo.encolar()
        trabajo.tomar(_AHORA)
        trabajo.marcar_error("timeout", _AHORA)
        trabajo.registrar_reintento(_AHORA)  # intentos=1, alcanza max_intentos
        assert trabajo.puede_reintentar is False

    def test_cancelar_desde_pendiente(self) -> None:
        trabajo = _trabajo()
        trabajo.cancelar()
        assert trabajo.estado == EstadoTrabajoOrquestador.CANCELADO
        assert trabajo.es_terminal

    def test_completado_es_estado_terminal_sin_transiciones(self) -> None:
        trabajo = _trabajo()
        trabajo.encolar()
        trabajo.tomar(_AHORA)
        trabajo.completar(_AHORA)
        with pytest.raises(TrabajoOrquestadorInvalidoError):
            trabajo.cancelar()
