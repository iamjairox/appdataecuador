"""Tests: ForoAbogadosAdapter -- Submodulos 8.2/8.9. "No asumir aun como
responde el Foro" -- se prueba con varias formas de respuesta plausibles,
todas mockeadas (sin red real), y con la deteccion defensiva completa:
CAPTCHA, timeout, pagina vacia, errores HTTP, reintentos, circuit breaker."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from govdata.domain.entities.persona import Persona
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import (
    ConsultaForoFallidaError,
    ConsultaForoPermanenteError,
    ForoCircuitoAbiertoError,
)
from govdata.domain.rules.reglas_foro import CatalogoCamposForo, ReglasCircuitoForo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.infrastructure.http.foro_abogados_adapter import ForoAbogadosAdapter

_CATALOGO = CatalogoCamposForo(
    campo_por_etiqueta={"NO REGISTRO": "registro", "PROVINCIA": "provincia", "ESTADO": "estado"}
)
_TABLA_VALIDA = """
<table>
    <tr><td>No. Registro</td><td>R-1</td></tr>
    <tr><td>Provincia</td><td>Pichincha</td></tr>
    <tr><td>Estado</td><td>Vigente</td></tr>
</table>
"""


def _respuesta(status_code: int = 200, texto: str = _TABLA_VALIDA) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = texto
    return resp


def _adaptador(**kwargs) -> ForoAbogadosAdapter:
    return ForoAbogadosAdapter(base_url="https://x.test", catalogo_campos=_CATALOGO, **kwargs)


class TestBuscarPorCedula:
    def test_forma_estandar_con_tabla(self) -> None:
        adaptador = _adaptador()
        with patch.object(adaptador._sesion, "get", return_value=_respuesta()):
            resultado = adaptador.buscar_por_cedula("0999999999")
        assert len(resultado) == 1
        assert resultado[0].registro == "R-1"

    def test_sin_resultados_retorna_lista_vacia(self) -> None:
        adaptador = _adaptador()
        with patch.object(adaptador._sesion, "get", return_value=_respuesta(texto="No se encontraron resultados para la busqueda")):
            assert adaptador.buscar_por_cedula("0999999999") == []

    def test_pagina_sin_campos_reconocidos_retorna_lista_vacia(self) -> None:
        adaptador = _adaptador()
        with patch.object(adaptador._sesion, "get", return_value=_respuesta(texto="<html><body>Contenido irrelevante largo</body></html>")):
            assert adaptador.buscar_por_cedula("0999999999") == []


class TestDeteccionDefensiva:
    def test_captcha_detectado_lanza_error_permanente(self) -> None:
        adaptador = _adaptador()
        with (
            patch.object(adaptador._sesion, "get", return_value=_respuesta(texto="Por favor resuelva el CAPTCHA para continuar")),
            pytest.raises(ConsultaForoPermanenteError),
        ):
            adaptador.buscar_por_cedula("0999999999")

    def test_pagina_vacia_lanza_error_transitorio(self) -> None:
        adaptador = _adaptador()
        with (
            patch.object(adaptador._sesion, "get", return_value=_respuesta(texto="   ")),
            pytest.raises(ConsultaForoFallidaError),
        ):
            adaptador.buscar_por_cedula("0999999999")

    def test_mensaje_de_error_transitorio_se_detecta(self) -> None:
        adaptador = _adaptador()
        with (
            patch.object(adaptador._sesion, "get", return_value=_respuesta(texto="Ocurrio un error interno, intente mas tarde")),
            pytest.raises(ConsultaForoFallidaError),
        ):
            adaptador.buscar_por_cedula("0999999999")

    def test_timeout_lanza_error_transitorio(self) -> None:
        adaptador = _adaptador()
        with (
            patch.object(adaptador._sesion, "get", side_effect=requests.Timeout("timeout")),
            pytest.raises(ConsultaForoFallidaError),
        ):
            adaptador.buscar_por_cedula("0999999999")

    def test_error_de_red_lanza_error_transitorio(self) -> None:
        adaptador = _adaptador()
        with (
            patch.object(adaptador._sesion, "get", side_effect=requests.ConnectionError("sin red")),
            pytest.raises(ConsultaForoFallidaError),
        ):
            adaptador.buscar_por_cedula("0999999999")

    def test_error_5xx_es_transitorio(self) -> None:
        adaptador = _adaptador()
        with (
            patch.object(adaptador._sesion, "get", return_value=_respuesta(status_code=503)),
            pytest.raises(ConsultaForoFallidaError),
        ):
            adaptador.buscar_por_cedula("0999999999")

    def test_404_retorna_lista_vacia(self) -> None:
        adaptador = _adaptador()
        with patch.object(adaptador._sesion, "get", return_value=_respuesta(status_code=404, texto="pagina no encontrada de longitud suficiente")):
            assert adaptador.buscar_por_cedula("0999999999") == []

    def test_400_es_error_permanente(self) -> None:
        adaptador = _adaptador()
        with (
            patch.object(adaptador._sesion, "get", return_value=_respuesta(status_code=400)),
            pytest.raises(ConsultaForoPermanenteError),
        ):
            adaptador.buscar_por_cedula("0999999999")


class TestReintentos:
    def test_reintenta_ante_error_transitorio_y_finalmente_tiene_exito(self) -> None:
        adaptador = _adaptador(max_reintentos=3, backoff_base_segundos=0.001)
        respuestas = [requests.ConnectionError("temporal"), _respuesta()]
        with patch.object(adaptador._sesion, "get", side_effect=respuestas) as mock_get:
            resultado = adaptador.buscar_por_cedula("0999999999")
        assert len(resultado) == 1
        assert mock_get.call_count == 2

    def test_nunca_reintenta_un_error_permanente(self) -> None:
        adaptador = _adaptador(max_reintentos=3, backoff_base_segundos=0.001)
        with (
            patch.object(adaptador._sesion, "get", return_value=_respuesta(status_code=400)) as mock_get,
            pytest.raises(ConsultaForoPermanenteError),
        ):
            adaptador.buscar_por_cedula("0999999999")
        assert mock_get.call_count == 1


class TestCircuitBreaker:
    def test_circuito_se_abre_tras_fallos_consecutivos_y_rechaza_sin_llamar_a_la_red(self) -> None:
        adaptador = _adaptador(
            reglas_circuito=ReglasCircuitoForo(umbral_fallos=2, segundos_enfriamiento=999.0),
            max_reintentos=1,
        )
        with patch.object(adaptador._sesion, "get", side_effect=requests.ConnectionError("caido")) as mock_get:
            for _ in range(2):
                with pytest.raises(ConsultaForoFallidaError):
                    adaptador.buscar_por_cedula("0999999999")
            llamadas_antes = mock_get.call_count
            with pytest.raises(ForoCircuitoAbiertoError):
                adaptador.buscar_por_cedula("0999999999")
            assert mock_get.call_count == llamadas_antes  # no se intento la red


class TestLas3FormasDeConsulta:
    def test_buscar_por_persona_con_cedula_usa_cedula(self) -> None:
        adaptador = _adaptador()
        persona = Persona(nombre_completo=NombreCompleto("Juan", "Perez"), cedula="0999999999")
        with patch.object(adaptador._sesion, "get", return_value=_respuesta()) as mock_get:
            adaptador.buscar_por_persona(persona)
        assert mock_get.call_args.kwargs["params"] == {"cedula": "0999999999"}

    def test_buscar_por_persona_sin_cedula_usa_nombre(self) -> None:
        adaptador = _adaptador()
        persona = Persona(nombre_completo=NombreCompleto("Juan", "Perez"))
        with patch.object(adaptador._sesion, "get", return_value=_respuesta()) as mock_get:
            adaptador.buscar_por_persona(persona)
        assert mock_get.call_args.kwargs["params"] == {
            "nombres": persona.nombre_completo.nombres, "apellidos": persona.nombre_completo.apellidos,
        }

    def test_buscar_por_persona_master_usa_nombre(self) -> None:
        adaptador = _adaptador()
        persona_master = PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Ana", "Gomez"))
        with patch.object(adaptador._sesion, "get", return_value=_respuesta()) as mock_get:
            adaptador.buscar_por_persona_master(persona_master)
        assert mock_get.call_args.kwargs["params"] == {
            "nombres": persona_master.nombre_completo.nombres, "apellidos": persona_master.nombre_completo.apellidos,
        }

    def test_cerrar_cierra_la_sesion(self) -> None:
        adaptador = _adaptador()
        with patch.object(adaptador._sesion, "close") as mock_close:
            adaptador.cerrar()
        mock_close.assert_called_once()
