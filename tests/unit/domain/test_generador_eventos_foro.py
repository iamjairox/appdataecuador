"""Tests: generador de Eventos del Foro -- Submodulo 8.7."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.diferencia_registro_foro_dto import DiferenciaRegistroForoDTO
from govdata.domain.rules.generador_eventos_foro import (
    generar_evento_consulta_exitosa,
    generar_evento_consulta_fallida,
    generar_eventos_por_diferencia,
)
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo
from govdata.domain.value_objects.tipo_evento_foro import TipoEventoForo

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestGenerarEventosPorDiferencia:
    def test_dato_nuevo(self) -> None:
        diferencia = DiferenciaRegistroForoDTO(tipo_cambio=TipoCambioForo.DATO_NUEVO, clave_registro="r1")
        eventos = generar_eventos_por_diferencia(diferencia, 1, _AHORA)
        assert len(eventos) == 1
        assert eventos[0].tipo == TipoEventoForo.REGISTRO_NUEVO

    def test_cambio_provincia(self) -> None:
        diferencia = DiferenciaRegistroForoDTO(tipo_cambio=TipoCambioForo.CAMBIO_PROVINCIA, clave_registro="r1")
        eventos = generar_eventos_por_diferencia(diferencia, 1, _AHORA)
        assert eventos[0].tipo == TipoEventoForo.CAMBIO_PROVINCIA

    def test_sin_cambios_no_genera_eventos(self) -> None:
        diferencia = DiferenciaRegistroForoDTO(tipo_cambio=TipoCambioForo.SIN_CAMBIOS, clave_registro="r1")
        assert generar_eventos_por_diferencia(diferencia, 1, _AHORA) == []


class TestEventosDeConsulta:
    def test_consulta_exitosa(self) -> None:
        evento = generar_evento_consulta_exitosa(1, _AHORA, 3)
        assert evento.tipo == TipoEventoForo.CONSULTA_EXITOSA
        assert evento.payload == {"registros_encontrados": 3}

    def test_consulta_fallida(self) -> None:
        evento = generar_evento_consulta_fallida(1, _AHORA, "timeout")
        assert evento.tipo == TipoEventoForo.CONSULTA_FALLIDA
        assert evento.payload == {"error": "timeout"}
