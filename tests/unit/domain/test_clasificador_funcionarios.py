"""Tests: Clasificador Inteligente (Submodulo 4.3)."""

from __future__ import annotations

import pytest

from govdata.application.dto.fila_extraida_dto import FilaExtraidaDTO
from govdata.application.dto.funcionario_clasificado_dto import (
    MotivoClasificacion,
    NivelConfianzaClasificacion,
)
from govdata.domain.rules.clasificador_funcionarios import clasificar_funcionario
from govdata.domain.rules.reglas_configurables import ReglasClasificacion


def _reglas(umbral: float = 80.0, alta: float = 92.0, media: float = 80.0) -> ReglasClasificacion:
    return ReglasClasificacion(
        umbral_score_minimo=umbral,
        nivel_alta=alta,
        nivel_media=media,
        cargos_por_area={
            "juridica": ["Director Juridico", "Asesor Juridico", "Abogado"],
            "financiera": ["Director Financiero"],
        },
    )


def _fila(cargo: str) -> FilaExtraidaDTO:
    return FilaExtraidaDTO(nombres="Juan", apellidos="Perez", cargo=cargo, dependencia="X")


class TestClasificarFuncionario:
    def test_cargo_exacto_area_juridica(self) -> None:
        resultado = clasificar_funcionario(_fila("Director Juridico"), _reglas())
        assert resultado is not None
        assert resultado.area == "juridica"
        assert resultado.score == 100.0
        assert resultado.nivel_confianza == NivelConfianzaClasificacion.ALTA

    def test_cargo_exacto_area_financiera(self) -> None:
        resultado = clasificar_funcionario(_fila("Director Financiero"), _reglas())
        assert resultado is not None
        assert resultado.area == "financiera"

    def test_cargo_no_especializado_se_conserva_como_general(self) -> None:
        resultado = clasificar_funcionario(_fila("Chofer"), _reglas())
        assert resultado is not None
        assert resultado.area == "general"
        assert resultado.motivo_clasificacion == MotivoClasificacion.SIN_AREA_ESPECIALIZADA

    def test_cargo_vacio_se_descarta(self) -> None:
        assert clasificar_funcionario(_fila(""), _reglas()) is None

    def test_nivel_confianza_media(self) -> None:
        """'Asesor Juridico Senior' vs 'Asesor Juridico': ~81 de similitud,
        por encima del umbral (80) pero por debajo de 'alta' (92)."""
        resultado = clasificar_funcionario(_fila("Asesor Juridico Senior"), _reglas())
        assert resultado is not None
        assert resultado.nivel_confianza == NivelConfianzaClasificacion.MEDIA

    def test_umbral_configurable_mas_estricto_rechaza(self) -> None:
        resultado = clasificar_funcionario(_fila("Asesor Legal Junior"), _reglas(umbral=99.0))
        assert resultado is not None
        assert resultado.area == "general"

    def test_umbral_configurable_mas_laxo_acepta(self) -> None:
        resultado = clasificar_funcionario(_fila("Abogado"), _reglas(umbral=10.0))
        assert resultado is not None


class TestClasificacionConReglasReales:
    """Casos observados en el muestreo real del numeral 2 DPE (2026-09-27),
    contra `config/rules/clasificacion_areas.yaml` real."""

    @staticmethod
    def _clasificar(cargo: str, dependencia: str = ""):
        from govdata.config.rule_engine import cargar_rule_engine

        fila = FilaExtraidaDTO(nombres="Juan", apellidos="Perez", cargo=cargo, dependencia=dependencia)
        return clasificar_funcionario(fila, cargar_rule_engine().clasificacion)

    @pytest.mark.parametrize(
        "cargo",
        [
            "PROCURADOR SINDICO",
            "SUB PROCURADOR SINDICO",
            "PROCURADORA SÍNDICA MUNICIPAL",
            "ABOGADO JUNIOR",
            "JEFE DE PATROCINIO",
            "ANALISTA DE PATROCINIO 2",
            "DIRECTOR/A DE ASESORIA LEGAL Y PATROCINIO",
            "ANALISTA JURÍDICO 1",
            "ESPECIALISTA JURIDICO DE CONTRATACION PUBLICA",
        ],
    )
    def test_cargo_juridico_real(self, cargo: str) -> None:
        resultado = self._clasificar(cargo)
        assert resultado is not None
        assert resultado.area == "juridica"
        assert resultado.motivo_clasificacion in (
            MotivoClasificacion.CARGO_SIMILAR,
            MotivoClasificacion.CARGO_PALABRA_CLAVE,
        )

    @pytest.mark.parametrize(
        ("cargo", "dependencia"),
        [
            ("JEFE DE LEGALIZACION", "DIRECCION DE AVALUOS Y CATASTROS"),
            ("REPRESENTANTE LEGAL", "GERENCIA GENERAL"),
            ("AGENTE MUNICIPAL", "DIRECCION DE PROCURADURIA SINDICA"),
            ("POLICIA MUNICIPAL", "PROCURADURIA SINDICA"),
            ("CONDUCTOR DE AUTOMOTOR 1", "DIRECCION DE PATROCINIO Y COACTIVAS"),
            ("ASISTENTE ADMINISTRATIVO 3", "DIRECCION DE ASESORIA JURIDICA"),
            ("COORDINADOR DE SEGURIDAD Y DE AGENTES DE CONTROL", "DIRECCION DE PROCURADURIA SINDICA"),
            ("ANALISTA DE CONTRATACION DE BIENES Y SERVICIOS", "DIRECCION DE PATROCINIO Y COACTIVAS"),
        ],
    )
    def test_falsos_positivos_reales_quedan_fuera(self, cargo: str, dependencia: str) -> None:
        resultado = self._clasificar(cargo, dependencia)
        assert resultado is None or resultado.area != "juridica"

    def test_director_en_direccion_juridica_se_clasifica_por_dependencia(self) -> None:
        resultado = self._clasificar("DIRECTOR", "DIRECCION DE ASESORIA JURIDICA")
        assert resultado is not None
        assert resultado.area == "juridica"
        assert resultado.motivo_clasificacion == MotivoClasificacion.DEPENDENCIA
        assert resultado.nivel_confianza == NivelConfianzaClasificacion.BAJA

    def test_jefe_de_division_en_procuraduria(self) -> None:
        resultado = self._clasificar("JEFE DE DIVISION", "PROCURADURIA SINDICA")
        assert resultado is not None
        assert resultado.motivo_clasificacion == MotivoClasificacion.DEPENDENCIA

    def test_financiera_no_usa_palabra_clave_ni_dependencia(self) -> None:
        resultado = self._clasificar("ANALISTA LEGAL DEL SECTOR FINANCIERO")
        assert resultado is None or resultado.area != "financiera"
