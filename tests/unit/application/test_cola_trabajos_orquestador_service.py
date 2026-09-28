"""Tests: ColaTrabajosOrquestadorService -- Submodulos 9.6/9.7/9.8."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.services.cola_trabajos_orquestador_service import (
    ColaTrabajosOrquestadorService,
)
from govdata.domain.value_objects.estado_trabajo_orquestador import EstadoTrabajoOrquestador
from govdata.domain.value_objects.nivel_prioridad_ejecucion import NivelPrioridadEjecucion
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador
from tests.unit.application.fakes_modulo9 import FakeTrabajoOrquestadorRepository

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _servicio() -> tuple[ColaTrabajosOrquestadorService, FakeTrabajoOrquestadorRepository]:
    repo = FakeTrabajoOrquestadorRepository()
    return ColaTrabajosOrquestadorService(repo, ahora_provider=lambda: _AHORA), repo


class TestEncolarYTomar:
    def test_encolar_deja_el_trabajo_en_cola(self) -> None:
        servicio, _repo = _servicio()
        trabajo = servicio.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": "X"}, "consulta_rapida")
        assert trabajo.estado == EstadoTrabajoOrquestador.EN_COLA

    def test_tomar_siguiente_respeta_prioridad(self) -> None:
        servicio, _repo = _servicio()
        servicio.encolar(
            TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": "baja"}, "consulta_rapida",
            prioridad=NivelPrioridadEjecucion.BAJA,
        )
        alta = servicio.encolar(
            TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": "alta"}, "consulta_rapida",
            prioridad=NivelPrioridadEjecucion.MUY_ALTA,
        )
        tomado = servicio.tomar_siguiente()
        assert tomado is not None
        assert tomado.id == alta.id
        assert tomado.estado == EstadoTrabajoOrquestador.EJECUTANDO

    def test_tomar_siguiente_sin_candidatos_retorna_none(self) -> None:
        servicio, _repo = _servicio()
        assert servicio.tomar_siguiente() is None

    def test_dos_workers_nunca_toman_el_mismo_trabajo(self) -> None:
        servicio, _repo = _servicio()
        servicio.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": "X"}, "consulta_rapida")

        primero = servicio.tomar_siguiente()
        segundo = servicio.tomar_siguiente()
        assert primero is not None
        assert segundo is None  # ya no hay candidatos EN_COLA/REINTENTANDO


class TestCicloDeVida:
    def test_completar(self) -> None:
        servicio, _repo = _servicio()
        trabajo = servicio.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {}, "consulta_rapida")
        servicio.iniciar_directo(trabajo)
        completado = servicio.marcar_completado(trabajo)
        assert completado.estado == EstadoTrabajoOrquestador.COMPLETADO

    def test_marcar_error_y_reintentar(self) -> None:
        servicio, _repo = _servicio()
        trabajo = servicio.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {}, "consulta_rapida")
        servicio.iniciar_directo(trabajo)
        servicio.marcar_error(trabajo, "timeout")
        assert trabajo.estado == EstadoTrabajoOrquestador.ERROR

        reintentado = servicio.reintentar_si_corresponde(trabajo)
        assert reintentado is True
        assert trabajo.estado == EstadoTrabajoOrquestador.REINTENTANDO

    def test_reintentar_agotado_retorna_false(self) -> None:
        servicio, _repo = _servicio()
        trabajo = servicio.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {}, "consulta_rapida", max_intentos=1)
        servicio.iniciar_directo(trabajo)
        servicio.marcar_error(trabajo, "timeout")
        servicio.reintentar_si_corresponde(trabajo)  # intentos=1, agota
        assert servicio.reintentar_si_corresponde(trabajo) is False

    def test_pausar_y_cancelar(self) -> None:
        servicio, _repo = _servicio()
        trabajo = servicio.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {}, "consulta_rapida")
        servicio.pausar(trabajo)
        assert trabajo.estado == EstadoTrabajoOrquestador.PAUSADO
        servicio.cancelar(trabajo)
        assert trabajo.estado == EstadoTrabajoOrquestador.CANCELADO


class TestReanudarInterrumpidos:
    def test_trabajos_ejecutando_se_reencolan(self) -> None:
        servicio, _repo = _servicio()
        trabajo = servicio.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {}, "consulta_rapida")
        servicio.iniciar_directo(trabajo)
        assert trabajo.estado == EstadoTrabajoOrquestador.EJECUTANDO

        cantidad = servicio.reanudar_interrumpidos()
        assert cantidad == 1
        recargado = servicio.buscar_por_id(trabajo.id)
        assert recargado is not None
        assert recargado.estado == EstadoTrabajoOrquestador.EN_COLA

    def test_sin_interrumpidos_retorna_cero(self) -> None:
        servicio, _repo = _servicio()
        assert servicio.reanudar_interrumpidos() == 0
