"""Tests: SenescytAdapter -- Submodulo 7.2. "No asumir aun como responde
SENESCYT" -- se prueba con varias formas de respuesta plausibles, todas
mockeadas (sin red real)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.domain.exceptions.domain_exceptions import ConsultaSenescytFallidaError
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.infrastructure.http.senescyt_adapter import SenescytAdapter


def _respuesta(status_code: int = 200, json_data: object = None, lanza_json_error: bool = False) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    if lanza_json_error:
        resp.json.side_effect = ValueError("no es JSON")
    else:
        resp.json.return_value = json_data
    return resp


class TestConsultarPorCedula:
    def test_forma_estandar_con_clave_titulos(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        datos = {"titulos": [{"titulo": "Abogado", "nivel": "Tercer Nivel", "institucion": "UCE", "numero_registro": "R1"}]}
        with patch.object(adaptador._sesion, "get", return_value=_respuesta(json_data=datos)):
            resultado = adaptador.consultar_por_cedula("0999999999")
        assert len(resultado) == 1
        assert resultado[0].titulo == "Abogado"
        assert resultado[0].numero_registro == "R1"

    def test_lista_cruda_en_la_raiz(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        datos = [{"titulo": "Medico", "nivel": "Tercer Nivel", "institucion": "PUCE"}]
        with patch.object(adaptador._sesion, "get", return_value=_respuesta(json_data=datos)):
            resultado = adaptador.consultar_por_cedula("0999999999")
        assert len(resultado) == 1
        assert resultado[0].titulo == "Medico"

    def test_nombres_de_campo_alternativos(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        datos = {"resultados": [{"nombre_titulo": "Ingeniero", "nivel_formacion": "Tercer Nivel", "universidad": "EPN"}]}
        with patch.object(adaptador._sesion, "get", return_value=_respuesta(json_data=datos)):
            resultado = adaptador.consultar_por_cedula("0999999999")
        assert resultado[0].titulo == "Ingeniero"
        assert resultado[0].institucion == "EPN"

    def test_item_sin_campos_obligatorios_se_descarta(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        datos = {"titulos": [{"titulo": "Abogado"}]}  # falta nivel/institucion
        with patch.object(adaptador._sesion, "get", return_value=_respuesta(json_data=datos)):
            resultado = adaptador.consultar_por_cedula("0999999999")
        assert resultado == []

    def test_sin_titulos_lista_vacia(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        with patch.object(adaptador._sesion, "get", return_value=_respuesta(json_data={"titulos": []})):
            assert adaptador.consultar_por_cedula("0999999999") == []


class TestErrores:
    def test_error_de_red_lanza_excepcion_de_dominio(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        with (
            patch.object(adaptador._sesion, "get", side_effect=requests.ConnectionError("no hay red")),
            pytest.raises(ConsultaSenescytFallidaError),
        ):
            adaptador.consultar_por_cedula("0999999999")

    def test_error_5xx_es_transitorio(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        with (
            patch.object(adaptador._sesion, "get", return_value=_respuesta(status_code=503)),
            pytest.raises(ConsultaSenescytFallidaError),
        ):
            adaptador.consultar_por_cedula("0999999999")

    def test_404_retorna_lista_vacia(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        with patch.object(adaptador._sesion, "get", return_value=_respuesta(status_code=404)):
            assert adaptador.consultar_por_cedula("0999999999") == []

    def test_400_lanza_excepcion(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        with (
            patch.object(adaptador._sesion, "get", return_value=_respuesta(status_code=400)),
            pytest.raises(ConsultaSenescytFallidaError),
        ):
            adaptador.consultar_por_cedula("0999999999")

    def test_respuesta_no_json_lanza_excepcion(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        with (
            patch.object(adaptador._sesion, "get", return_value=_respuesta(lanza_json_error=True)),
            pytest.raises(ConsultaSenescytFallidaError),
        ):
            adaptador.consultar_por_cedula("0999999999")

    def test_forma_no_reconocida_lanza_excepcion(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        with (
            patch.object(adaptador._sesion, "get", return_value=_respuesta(json_data="texto plano")),
            pytest.raises(ConsultaSenescytFallidaError),
        ):
            adaptador.consultar_por_cedula("0999999999")


class TestLas4FormasDeConsulta:
    def test_consultar_por_nombres(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        with patch.object(adaptador._sesion, "get", return_value=_respuesta(json_data={"titulos": []})) as mock_get:
            adaptador.consultar_por_nombres("Juan", "Perez")
        assert mock_get.call_args.kwargs["params"] == {"nombres": "Juan", "apellidos": "Perez"}

    def test_consultar_por_identidad(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        senales = SenalesIdentidadDTO(nombre="Juan", apellido="Perez")
        with patch.object(adaptador._sesion, "get", return_value=_respuesta(json_data={"titulos": []})):
            resultado = adaptador.consultar_por_identidad(senales)
        assert resultado == []

    def test_consultar_por_persona_master(self) -> None:
        from govdata.domain.entities.persona_master import PersonaMaster
        from govdata.domain.value_objects.nombre_completo import NombreCompleto

        adaptador = SenescytAdapter(base_url="https://x.test")
        persona_master = PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"))
        with patch.object(adaptador._sesion, "get", return_value=_respuesta(json_data={"titulos": []})):
            resultado = adaptador.consultar_por_persona_master(persona_master)
        assert resultado == []

    def test_fuente_es_senescyt(self) -> None:
        adaptador = SenescytAdapter(base_url="https://x.test")
        assert adaptador.fuente == FuenteExterna.SENESCYT


class TestConsultarGenerico:
    def test_consultar_cumple_external_source_port(self) -> None:
        """Compatibilidad opcional con el pipeline generico de Modulo 6."""
        adaptador = SenescytAdapter(base_url="https://x.test")
        senales = SenalesIdentidadDTO(nombre="Juan", apellido="Perez")
        datos = {"titulos": [{"titulo": "Abogado", "nivel": "Tercer Nivel", "institucion": "UCE"}]}
        with patch.object(adaptador._sesion, "get", return_value=_respuesta(json_data=datos)):
            resultado = adaptador.consultar(senales)
        assert resultado.encontrado is True
        assert resultado.fuente == FuenteExterna.SENESCYT
