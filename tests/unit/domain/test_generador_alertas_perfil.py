"""Tests: generador de Alertas de Perfil (Submodulo 6.13)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.domain.rules.generador_alertas_perfil import (
    generar_alerta_por_cambio,
    generar_alertas_por_cambios,
)
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_perfil import TipoAlertaPerfil

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestGenerarAlertaPorCambio:
    def test_titulo_cambiado(self) -> None:
        alerta = generar_alerta_por_cambio("titulo", "Abogado", "Doctor en Jurisprudencia", 1, _AHORA)
        assert alerta is not None
        assert alerta.tipo == TipoAlertaPerfil.TITULO_CAMBIADO
        assert alerta.prioridad == NivelCriticidad.MEDIO

    def test_nueva_maestria(self) -> None:
        alerta = generar_alerta_por_cambio("maestria", None, "Maestria en Derecho Penal", 1, _AHORA)
        assert alerta is not None
        assert alerta.tipo == TipoAlertaPerfil.NUEVA_MAESTRIA
        assert alerta.prioridad == NivelCriticidad.ALTO

    def test_cambio_correo_perfil(self) -> None:
        alerta = generar_alerta_por_cambio("correo", "viejo@x.com", "nuevo@x.com", 1, _AHORA)
        assert alerta is not None
        assert alerta.tipo == TipoAlertaPerfil.CAMBIO_CORREO_PERFIL

    def test_campo_no_reconocido_no_genera_alerta(self) -> None:
        assert generar_alerta_por_cambio("campo_desconocido", "a", "b", 1, _AHORA) is None

    def test_sin_cambio_real_no_genera_alerta(self) -> None:
        assert generar_alerta_por_cambio("titulo", "Abogado", "Abogado", 1, _AHORA) is None

    def test_valor_nuevo_vacio_no_genera_alerta(self) -> None:
        assert generar_alerta_por_cambio("titulo", "Abogado", None, 1, _AHORA) is None


class TestGenerarAlertasPorCambios:
    def test_multiples_cambios_generan_multiples_alertas(self) -> None:
        cambios = {
            "titulo": (None, "Abogado"),
            "correo": ("a@x.com", "b@x.com"),
            "campo_irrelevante": ("x", "y"),
        }
        alertas = generar_alertas_por_cambios(cambios, 1, _AHORA)
        tipos = {a.tipo for a in alertas}
        assert tipos == {TipoAlertaPerfil.TITULO_CAMBIADO, TipoAlertaPerfil.CAMBIO_CORREO_PERFIL}

    def test_sin_cambios_reconocidos_retorna_lista_vacia(self) -> None:
        assert generar_alertas_por_cambios({}, 1, _AHORA) == []
