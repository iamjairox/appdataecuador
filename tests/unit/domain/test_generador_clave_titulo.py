"""Tests: generador de clave de titulo (Submodulo 7.7, base de emparejamiento)."""

from __future__ import annotations

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.domain.rules.generador_clave_titulo import generar_clave_titulo


def _dto(**kwargs) -> PersonaAcademicaDTO:
    base = {"titulo": "Abogado", "nivel": "Tercer Nivel", "institucion": "UCE", "numero_registro": None}
    base.update(kwargs)
    return PersonaAcademicaDTO(**base)


class TestGenerarClaveTitulo:
    def test_con_numero_registro_usa_ese_valor_normalizado(self) -> None:
        clave = generar_clave_titulo(_dto(numero_registro="1234-56"))
        assert clave == "registro:1234 56"  # normalizar_texto colapsa '-' a espacio

    def test_con_numero_registro_es_determinista(self) -> None:
        assert generar_clave_titulo(_dto(numero_registro="ABC")) == generar_clave_titulo(_dto(numero_registro="ABC"))

    def test_sin_numero_registro_usa_hash_de_titulo_institucion_nivel(self) -> None:
        clave = generar_clave_titulo(_dto())
        assert clave.startswith("sin_registro:")

    def test_sin_numero_registro_es_determinista(self) -> None:
        assert generar_clave_titulo(_dto()) == generar_clave_titulo(_dto())

    def test_sin_numero_registro_titulos_distintos_generan_claves_distintas(self) -> None:
        assert generar_clave_titulo(_dto(titulo="Abogado")) != generar_clave_titulo(_dto(titulo="Ingeniero"))

    def test_numero_registro_vacio_se_trata_como_ausente(self) -> None:
        clave = generar_clave_titulo(_dto(numero_registro="   "))
        assert clave.startswith("sin_registro:")
