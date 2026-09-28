"""Tests: Value Objects de dominio."""

from __future__ import annotations

import pytest

from govdata.domain.exceptions.domain_exceptions import ValorInvalidoError
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.cargo import Cargo
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.telefono import Telefono


class TestCorreo:
    def test_normaliza_a_minusculas(self) -> None:
        assert Correo(" Juan.Perez@DPE.GOB.EC ").valor == "juan.perez@dpe.gob.ec"

    def test_rechaza_correo_invalido(self) -> None:
        with pytest.raises(ValorInvalidoError):
            Correo("no-es-un-correo")

    def test_crear_opcional_retorna_none_si_vacio(self) -> None:
        assert Correo.crear_opcional("") is None
        assert Correo.crear_opcional(None) is None
        assert Correo.crear_opcional("N/A") is None

    def test_crear_opcional_retorna_correo_si_valido(self) -> None:
        assert Correo.crear_opcional("a@b.com") == Correo("a@b.com")


class TestTelefono:
    def test_normaliza_a_solo_digitos(self) -> None:
        assert Telefono("(02) 222-3344").valor == "022223344"

    def test_conserva_prefijo_internacional(self) -> None:
        assert Telefono("+593 99 123 4567").valor == "+593991234567"

    def test_rechaza_telefono_muy_corto(self) -> None:
        with pytest.raises(ValorInvalidoError):
            Telefono("123")

    def test_crear_opcional_retorna_none_si_vacio(self) -> None:
        assert Telefono.crear_opcional(None) is None


class TestNombreCompleto:
    def test_normaliza_tildes_y_mayusculas(self) -> None:
        nc = NombreCompleto(nombres="Juan Carlos", apellidos="Pérez")
        assert nc.nombres == "JUAN CARLOS"
        assert nc.apellidos == "PEREZ"
        assert nc.nombre_completo == "JUAN CARLOS PEREZ"

    def test_colapsa_espacios(self) -> None:
        nc = NombreCompleto(nombres="  Juan   Carlos  ", apellidos="Perez")
        assert nc.nombres == "JUAN CARLOS"

    def test_rechaza_nombres_vacios(self) -> None:
        with pytest.raises(ValorInvalidoError):
            NombreCompleto(nombres="", apellidos="Perez")


class TestCargo:
    def test_normaliza_a_title_case(self) -> None:
        assert Cargo("DIRECTOR JURÍDICO").valor == "Director Juridico"

    def test_rechaza_cargo_vacio(self) -> None:
        with pytest.raises(ValorInvalidoError):
            Cargo("   ")


class TestAreaRelevante:
    """El catalogo de cargos por area vive desde el Modulo 4 en
    `config/rules/clasificacion_areas.yaml` (Motor de Reglas) -- ver
    `tests/unit/domain/test_clasificador_funcionarios.py`. Aqui solo se
    prueba el enum en si (usado por el esquema de base de datos).
    """

    def test_valores_del_enum(self) -> None:
        assert AreaRelevante.JURIDICA.value == "juridica"
        assert AreaRelevante.FINANCIERA.value == "financiera"
