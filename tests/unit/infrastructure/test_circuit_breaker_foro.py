"""Tests: CircuitBreakerForo -- Submodulo 8.9."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from govdata.domain.rules.reglas_foro import ReglasCircuitoForo
from govdata.infrastructure.http.circuit_breaker_foro import CircuitBreakerForo, EstadoCircuito

_T0 = datetime(2026, 1, 1, tzinfo=UTC)


class _RelojControlado:
    def __init__(self, inicio: datetime) -> None:
        self.ahora = inicio

    def __call__(self) -> datetime:
        return self.ahora


class TestCircuitBreakerForo:
    def test_inicia_cerrado_y_permite_intentos(self) -> None:
        cb = CircuitBreakerForo(ReglasCircuitoForo(umbral_fallos=3))
        assert cb.estado == EstadoCircuito.CERRADO
        assert cb.permitir_intento() is True

    def test_abre_tras_alcanzar_el_umbral_de_fallos(self) -> None:
        cb = CircuitBreakerForo(ReglasCircuitoForo(umbral_fallos=3))
        cb.registrar_fallo()
        cb.registrar_fallo()
        assert cb.estado == EstadoCircuito.CERRADO
        cb.registrar_fallo()
        assert cb.estado == EstadoCircuito.ABIERTO
        assert cb.permitir_intento() is False

    def test_exito_resetea_el_contador_de_fallos(self) -> None:
        cb = CircuitBreakerForo(ReglasCircuitoForo(umbral_fallos=3))
        cb.registrar_fallo()
        cb.registrar_fallo()
        cb.registrar_exito()
        cb.registrar_fallo()
        cb.registrar_fallo()
        assert cb.estado == EstadoCircuito.CERRADO  # solo 2 fallos consecutivos tras el reset

    def test_pasa_a_semi_abierto_tras_el_enfriamiento(self) -> None:
        reloj = _RelojControlado(_T0)
        cb = CircuitBreakerForo(ReglasCircuitoForo(umbral_fallos=1, segundos_enfriamiento=30.0), ahora_provider=reloj)
        cb.registrar_fallo()
        assert cb.estado == EstadoCircuito.ABIERTO
        assert cb.permitir_intento() is False

        reloj.ahora = _T0 + timedelta(seconds=31)
        assert cb.permitir_intento() is True
        assert cb.estado == EstadoCircuito.SEMI_ABIERTO

    def test_fallo_en_semi_abierto_vuelve_a_abrir(self) -> None:
        reloj = _RelojControlado(_T0)
        cb = CircuitBreakerForo(ReglasCircuitoForo(umbral_fallos=1, segundos_enfriamiento=10.0), ahora_provider=reloj)
        cb.registrar_fallo()
        reloj.ahora = _T0 + timedelta(seconds=11)
        cb.permitir_intento()
        assert cb.estado == EstadoCircuito.SEMI_ABIERTO

        cb.registrar_fallo()
        assert cb.estado == EstadoCircuito.ABIERTO

    def test_exito_en_semi_abierto_cierra_el_circuito(self) -> None:
        reloj = _RelojControlado(_T0)
        cb = CircuitBreakerForo(ReglasCircuitoForo(umbral_fallos=1, segundos_enfriamiento=10.0), ahora_provider=reloj)
        cb.registrar_fallo()
        reloj.ahora = _T0 + timedelta(seconds=11)
        cb.permitir_intento()
        cb.registrar_exito()
        assert cb.estado == EstadoCircuito.CERRADO
