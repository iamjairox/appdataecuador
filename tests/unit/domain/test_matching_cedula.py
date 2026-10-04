from govdata.application.dto.identificacion_cedula_dto import (
    CedulaCandidateDTO,
    EstadoMatchingCedula,
)
from govdata.domain.rules.matching_cedula import (
    candidato_desde_fila_fuente,
    extraer_cedula,
    hacer_matching_cedula,
    normalizar_nombre,
)


def candidato(nombres: str, paterno: str = "AGUILAR", materno: str = "AGUAY") -> CedulaCandidateDTO:
    return CedulaCandidateDTO("0100000000", nombres, paterno, materno)


def test_normaliza_tildes_puntuacion_y_espacios() -> None:
    assert normalizar_nombre(" María,  Cristina  Aguilar-Aguay ") == "MARIA CRISTINA AGUILAR AGUAY"


def test_match_exacto_sin_depender_del_orden_de_caso() -> None:
    resultado = hacer_matching_cedula("María Cristina", "Aguilar Aguay", [candidato("MARIA CRISTINA")])
    assert resultado.estado == EstadoMatchingCedula.MATCH_EXACT
    assert resultado.candidato is not None


def test_no_selecciona_dos_coincidencias_exacto() -> None:
    resultado = hacer_matching_cedula("MARIA CRISTINA", "AGUILAR AGUAY", [candidato("MARIA CRISTINA"), candidato("MARIA CRISTINA")])
    assert resultado.estado == EstadoMatchingCedula.AMBIGUOUS
    assert resultado.candidato is None


def test_sin_candidatos_es_no_cedula_found() -> None:
    assert hacer_matching_cedula("A", "B", []).estado == EstadoMatchingCedula.NO_CEDULA_FOUND


def test_extrae_cedula_sin_separadores() -> None:
    assert extraer_cedula("010-123456-7") == "0101234567"
    assert extraer_cedula("Cédula") is None


def test_candidato_desde_fila_fuente() -> None:
    fila = candidato_desde_fila_fuente("0102030405", "AYALA SANTI DEXI VIRGINIA")
    assert fila is not None
    assert fila.cedula == "0102030405"
    assert fila.nombres == "DEXI VIRGINIA"
    assert fila.apellido_paterno == "AYALA SANTI"
