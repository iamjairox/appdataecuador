"""Tests: middleware (request-id, rate limit) -- Modulo 10, funciones/clases
puras (sin ASGI real)."""

from __future__ import annotations

from govdata.infrastructure.api.middleware.rate_limit import ContadorVentanaDeslizante
from govdata.infrastructure.api.middleware.request_id import _request_id_entrante_o_nuevo


class TestRequestIdEntranteONuevo:
    def test_reutiliza_un_request_id_valido(self) -> None:
        assert _request_id_entrante_o_nuevo("abc-123.def_456") == "abc-123.def_456"

    def test_genera_uno_nuevo_si_no_viene(self) -> None:
        generado = _request_id_entrante_o_nuevo(None)
        assert generado  # UUID4 no vacio

    def test_genera_uno_nuevo_si_el_entrante_tiene_caracteres_invalidos(self) -> None:
        generado = _request_id_entrante_o_nuevo("<script>alert(1)</script>")
        assert generado != "<script>alert(1)</script>"

    def test_genera_uno_nuevo_si_el_entrante_es_demasiado_largo(self) -> None:
        entrante = "a" * 200
        generado = _request_id_entrante_o_nuevo(entrante)
        assert generado != entrante


class TestContadorVentanaDeslizante:
    def test_permite_hasta_el_limite(self) -> None:
        contador = ContadorVentanaDeslizante(limite_por_minuto=2)
        assert contador.permitir("clave") is True
        assert contador.permitir("clave") is True
        assert contador.permitir("clave") is False

    def test_claves_distintas_tienen_contadores_independientes(self) -> None:
        contador = ContadorVentanaDeslizante(limite_por_minuto=1)
        assert contador.permitir("a") is True
        assert contador.permitir("b") is True

    def test_las_marcas_viejas_se_purgan_de_la_ventana(self, monkeypatch) -> None:
        """Cubre la rama de purga (`marcas.popleft()`): una marca de hace
        mas de 60s no cuenta contra el limite."""
        import govdata.infrastructure.api.middleware.rate_limit as modulo_rate_limit

        reloj = {"ahora": 0.0}
        monkeypatch.setattr(modulo_rate_limit.time, "monotonic", lambda: reloj["ahora"])

        contador = ContadorVentanaDeslizante(limite_por_minuto=1)
        assert contador.permitir("clave") is True
        assert contador.permitir("clave") is False  # ventana llena

        reloj["ahora"] = 61.0  # avanza mas alla de la ventana de 60s
        assert contador.permitir("clave") is True
