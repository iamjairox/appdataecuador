"""Tests: generador de Eventos Academicos (Submodulo 7.9)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.diferencia_titulo_dto import (
    CampoModificadoTituloDTO,
    DiferenciaTituloDTO,
)
from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.domain.rules.generador_eventos_academicos import (
    generar_evento_consulta_exitosa,
    generar_evento_consulta_fallida,
    generar_eventos_por_diferencia,
)
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico
from govdata.domain.value_objects.tipo_evento_academico import TipoEventoAcademico

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestEventosPorDiferencia:
    def test_titulo_nuevo(self) -> None:
        diferencia = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.TITULO_NUEVO, clave_titulo="x",
            datos_actuales=PersonaAcademicaDTO(titulo="ABOGADO", nivel="TERCER NIVEL", institucion="UCE"),
        )
        eventos = generar_eventos_por_diferencia(diferencia, 1, _AHORA)
        assert len(eventos) == 1
        assert eventos[0].tipo == TipoEventoAcademico.TITULO_NUEVO

    def test_titulo_eliminado(self) -> None:
        diferencia = DiferenciaTituloDTO(tipo_cambio=TipoCambioAcademico.TITULO_ELIMINADO, clave_titulo="x")
        eventos = generar_eventos_por_diferencia(diferencia, 1, _AHORA)
        assert eventos[0].tipo == TipoEventoAcademico.TITULO_ELIMINADO

    def test_cambio_multiple_genera_evento_por_campo(self) -> None:
        diferencia = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.CAMBIO_MULTIPLE, clave_titulo="x",
            campos_modificados=(
                CampoModificadoTituloDTO("nivel", "a", "b"),
                CampoModificadoTituloDTO("estado", "c", "d"),
            ),
        )
        eventos = generar_eventos_por_diferencia(diferencia, 1, _AHORA)
        tipos = {e.tipo for e in eventos}
        assert tipos == {TipoEventoAcademico.CAMBIO_NIVEL, TipoEventoAcademico.CAMBIO_ESTADO}

    def test_sin_cambios_no_genera_eventos(self) -> None:
        diferencia = DiferenciaTituloDTO(tipo_cambio=TipoCambioAcademico.SIN_CAMBIOS, clave_titulo="x")
        assert generar_eventos_por_diferencia(diferencia, 1, _AHORA) == []


class TestEventosDeConsulta:
    def test_consulta_exitosa(self) -> None:
        evento = generar_evento_consulta_exitosa(1, _AHORA, titulos_encontrados=3)
        assert evento.tipo == TipoEventoAcademico.CONSULTA_EXITOSA
        assert evento.payload["titulos_encontrados"] == 3

    def test_consulta_fallida(self) -> None:
        evento = generar_evento_consulta_fallida(1, _AHORA, "timeout")
        assert evento.tipo == TipoEventoAcademico.CONSULTA_FALLIDA
        assert evento.payload["error"] == "timeout"
