"""Tests para el motor de matching de cédulas mejorado.

El matching es deliberadamente conservador:
- Nunca se selecciona automáticamente el primer resultado
- Si hay dos candidatos plausibles, el resultado es AMBIGUOUS
- La identidad se basa en comparación normalizada del nombre completo
"""

from __future__ import annotations

from govdata.application.dto.identificacion_cedula_dto import (
    CedulaCandidateDTO,
    EstadoMatchingCedula,
)
from govdata.domain.rules.matching_cedula import hacer_matching_cedula, normalizar_nombre


def _candidato(cedula: str, nombres: str, apellido_paterno: str = "", apellido_materno: str = "") -> CedulaCandidateDTO:
    """Helper para crear un CedulaCandidateDTO."""
    return CedulaCandidateDTO(
        cedula=cedula,
        nombres=nombres,
        apellido_paterno=apellido_paterno,
        apellido_materno=apellido_materno,
    )


class TestNormalizarNombre:
    """Tests para la normalización de nombres."""

    def test_normalizar_mayusculas(self) -> None:
        assert normalizar_nombre("juan carlos") == "JUAN CARLOS"

    def test_normalizar_tildes(self) -> None:
        assert normalizar_nombre("Pérez") == "PEREZ"
        assert normalizar_nombre("González") == "GONZALEZ"

    def test_normalizar_espacios(self) -> None:
        assert normalizar_nombre("  juan   carlos  ") == "JUAN CARLOS"

    def test_normalizar_puntuacion(self) -> None:
        assert normalizar_nombre("juan-carlos") == "JUAN CARLOS"
        assert normalizar_nombre("juan.carlos") == "JUAN CARLOS"


class TestHacerMatchingCedula:
    """Tests para el motor de matching de cédulas."""

    def test_sin_candidatos(self) -> None:
        resultado = hacer_matching_cedula("DEXI VIRGINIA", "AYALA SANTI", [])
        assert resultado.estado == EstadoMatchingCedula.NO_CEDULA_FOUND

    def test_coincidencia_exacta(self) -> None:
        candidatos = [
            _candidato("1234567890", "DEXI VIRGINIA", "AYALA", "SANTI"),
        ]
        resultado = hacer_matching_cedula("DEXI VIRGINIA", "AYALA SANTI", candidatos)
        assert resultado.estado == EstadoMatchingCedula.MATCH_EXACT
        assert resultado.candidato is not None
        assert resultado.candidato.cedula == "1234567890"

    def test_coincidencia_exacta_con_orden_diferente(self) -> None:
        """El orden de los nombres no afecta la coincidencia exacta."""
        candidatos = [
            _candidato("1234567890", "AYALA SANTI", "DEXI", "VIRGINIA"),
        ]
        resultado = hacer_matching_cedula("DEXI VIRGINIA", "AYALA SANTI", candidatos)
        assert resultado.estado == EstadoMatchingCedula.MATCH_EXACT

    def test_coincidencia_alta(self) -> None:
        candidatos = [
            _candidato("1234567890", "DEXI VIRGINIA", "AYALA", "SANTI"),
        ]
        resultado = hacer_matching_cedula("DEXI VIRGINIA", "AYALA SANTI", candidatos)
        assert resultado.estado == EstadoMatchingCedula.MATCH_EXACT
        assert resultado.candidato is not None

    def test_caso_ambiguo_dos_candidatos_exactos(self) -> None:
        candidatos = [
            _candidato("1234567890", "DEXI VIRGINIA", "AYALA", "SANTI"),
            _candidato("0987654321", "AYALA SANTI", "DEXI", "VIRGINIA"),
        ]
        resultado = hacer_matching_cedula("DEXI VIRGINIA", "AYALA SANTI", candidatos)
        assert resultado.estado == EstadoMatchingCedula.AMBIGUOUS
        assert resultado.candidato is None
        assert len(resultado.candidatos) == 2

    def test_caso_ambiguo_dos_candidatos_altos(self) -> None:
        candidatos = [
            _candidato("1234567890", "DEXI VIRGINIA", "AYALA", "SANTI"),
            _candidato("0987654321", "VIRGINIA DEXI", "SANTI", "AYALA"),
        ]
        resultado = hacer_matching_cedula("DEXI VIRGINIA", "AYALA SANTI", candidatos)
        assert resultado.estado == EstadoMatchingCedula.AMBIGUOUS
        assert resultado.candidato is None

    def test_no_match(self) -> None:
        candidatos = [
            _candidato("1234567890", "JUAN CARLOS", "PEREZ", "GOMEZ"),
        ]
        resultado = hacer_matching_cedula("DEXI VIRGINIA", "AYALA SANTI", candidatos)
        assert resultado.estado == EstadoMatchingCedula.NO_MATCH

    def test_caso_real_ayala_santi(self) -> None:
        """Test con el caso real de AYALA SANTI.

        Entrada: "DEXI VIRGINIA AYALA SANTI"
        Candidatos:
            - "AYALA SANTI ALEXANDER RAFAEL"
            - "AYALA SANTI DEXI VIRGINIA"
            - "AYALA SANTI KEVIN XAVIER"
        Resultado esperado: MATCH_EXACT con "AYALA SANTI DEXI VIRGINIA"
        (el candidato tiene exactamente los mismos tokens, en diferente orden)
        """
        candidatos = [
            _candidato("1111111111", "ALEXANDER RAFAEL", "AYALA", "SANTI"),
            _candidato("2222222222", "DEXI VIRGINIA", "AYALA", "SANTI"),
            _candidato("3333333333", "KEVIN XAVIER", "AYALA", "SANTI"),
        ]
        resultado = hacer_matching_cedula("DEXI VIRGINIA", "AYALA SANTI", candidatos)
        assert resultado.estado == EstadoMatchingCedula.MATCH_EXACT
        assert resultado.candidato is not None
        assert resultado.candidato.cedula == "2222222222"

    def test_multiples_candidatos_con_uno_exacto(self) -> None:
        """Si hay un solo candidato exacto, se selecciona aunque haya otros candidatos."""
        candidatos = [
            _candidato("1111111111", "ALEXANDER RAFAEL", "AYALA", "SANTI"),
            _candidato("2222222222", "DEXI VIRGINIA", "AYALA", "SANTI"),
            _candidato("3333333333", "KEVIN XAVIER", "AYALA", "SANTI"),
        ]
        resultado = hacer_matching_cedula("DEXI VIRGINIA", "AYALA SANTI", candidatos)
        assert resultado.estado == EstadoMatchingCedula.MATCH_EXACT
        assert resultado.candidato is not None
        assert resultado.candidato.cedula == "2222222222"
