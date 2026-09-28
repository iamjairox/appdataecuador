"""Tests: Clasificador Inteligente (Submodulo 4.3)."""

from __future__ import annotations

from govdata.application.dto.fila_extraida_dto import FilaExtraidaDTO
from govdata.application.dto.funcionario_clasificado_dto import NivelConfianzaClasificacion
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

    def test_cargo_no_relevante_se_descarta(self) -> None:
        assert clasificar_funcionario(_fila("Chofer"), _reglas()) is None

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
        assert resultado is None

    def test_umbral_configurable_mas_laxo_acepta(self) -> None:
        resultado = clasificar_funcionario(_fila("Abogado"), _reglas(umbral=10.0))
        assert resultado is not None
