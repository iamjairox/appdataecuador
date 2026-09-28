"""Tests: generador de Eventos de Perfil (Submodulo 6.12)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.domain.rules.generador_eventos_perfil import (
    generar_evento_fuente_actualizada,
    generar_evento_nueva_fuente,
    generar_evento_persona_enriquecida,
    generar_evento_persona_fusionada,
    generar_eventos_por_cambios,
)
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.domain.value_objects.tipo_evento_identidad import TipoEventoIdentidad

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestEventosSimples:
    def test_persona_enriquecida(self) -> None:
        evento = generar_evento_persona_enriquecida(1, FuenteExterna.SENESCYT, _AHORA)
        assert evento.tipo == TipoEventoIdentidad.PERSONA_ENRIQUECIDA
        assert evento.payload["fuente"] == "senescyt"

    def test_persona_fusionada(self) -> None:
        evento = generar_evento_persona_fusionada(1, 2, 99.5, _AHORA)
        assert evento.tipo == TipoEventoIdentidad.PERSONA_FUSIONADA
        assert evento.persona_master_id == 1
        assert evento.payload["persona_master_absorbida_id"] == 2
        assert evento.payload["score"] == 99.5

    def test_nueva_fuente(self) -> None:
        evento = generar_evento_nueva_fuente(1, FuenteExterna.FORO_ABOGADOS, _AHORA)
        assert evento.tipo == TipoEventoIdentidad.NUEVA_FUENTE

    def test_fuente_actualizada(self) -> None:
        evento = generar_evento_fuente_actualizada(1, FuenteExterna.FORO_ABOGADOS, 3, _AHORA)
        assert evento.tipo == TipoEventoIdentidad.FUENTE_ACTUALIZADA
        assert evento.payload["version"] == 3


class TestEventosPorCambios:
    def test_nuevo_titulo(self) -> None:
        eventos = generar_eventos_por_cambios({"titulo": (None, "Abogado")}, 1, _AHORA)
        assert len(eventos) == 1
        assert eventos[0].tipo == TipoEventoIdentidad.NUEVO_TITULO

    def test_cambio_de_profesion(self) -> None:
        eventos = generar_eventos_por_cambios({"profesion": ("Ingeniero", "Abogado")}, 1, _AHORA)
        assert len(eventos) == 1
        assert eventos[0].tipo == TipoEventoIdentidad.CAMBIO_DE_PROFESION

    def test_campo_no_relevante_no_genera_evento(self) -> None:
        assert generar_eventos_por_cambios({"correo": ("a@x.com", "b@x.com")}, 1, _AHORA) == []

    def test_sin_cambio_real_no_genera_evento(self) -> None:
        assert generar_eventos_por_cambios({"titulo": ("Abogado", "Abogado")}, 1, _AHORA) == []
