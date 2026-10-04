"""Tests: Normalizador Universal (Submodulo 4.2)."""

from __future__ import annotations

import pytest

from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO
from govdata.domain.rules.normalizador_universal import (
    dividir_nombre_completo,
    limpiar_extension_telefonica,
    limpiar_telefono,
    normalizar_tabla,
)
from govdata.domain.rules.reglas_configurables import ReglasNormalizacion

_SINONIMOS = {
    "nombres": ["Nombres"],
    "apellidos": ["Apellidos"],
    "nombre_completo": ["Nombre Completo", "Servidor", "Apellidos y Nombres"],
    "cargo": ["Cargo", "Puesto"],
    "dependencia": ["Dependencia", "Unidad"],
    "correo": ["Correo", "Email"],
    "telefono": ["Telefono", "Celular"],
}


def _reglas() -> ReglasNormalizacion:
    return ReglasNormalizacion(sinonimos_por_campo=_SINONIMOS)


class TestDividirNombreCompleto:
    def test_cuatro_palabras_divide_por_mitad(self) -> None:
        assert dividir_nombre_completo("Juan Carlos Perez Gomez") == ("Juan Carlos", "Perez Gomez")

    def test_una_palabra(self) -> None:
        assert dividir_nombre_completo("Juan") == ("Juan", "")

    def test_tres_palabras_da_la_extra_a_nombres(self) -> None:
        assert dividir_nombre_completo("Juan Carlos Perez") == ("Juan Carlos", "Perez")

    def test_cadena_vacia(self) -> None:
        assert dividir_nombre_completo("") == ("", "")


class TestNormalizarTabla:
    def test_columnas_separadas(self) -> None:
        tabla = TablaExtraidaDTO(
            encabezados=("Nombres", "Apellidos", "Cargo", "Dependencia", "Correo", "Telefono"),
            filas=[
                {
                    "Nombres": "Juan",
                    "Apellidos": "Perez",
                    "Cargo": "Director Juridico",
                    "Dependencia": "Procuraduria",
                    "Correo": "jp@x.gob.ec",
                    "Telefono": "099",
                }
            ],
        )
        resultado = normalizar_tabla(tabla, _reglas())
        assert len(resultado) == 1
        assert resultado[0].nombres == "Juan"
        assert resultado[0].apellidos == "Perez"
        assert resultado[0].correo == "jp@x.gob.ec"

    def test_columna_combinada_se_divide(self) -> None:
        tabla = TablaExtraidaDTO(
            encabezados=("Servidor", "Cargo"),
            filas=[{"Servidor": "Juan Carlos Perez Gomez", "Cargo": "Director Juridico"}],
        )
        resultado = normalizar_tabla(tabla, _reglas())
        assert resultado[0].nombres == "Juan Carlos"
        assert resultado[0].apellidos == "Perez Gomez"

    def test_encabezados_desconocidos_descarta_la_fila(self) -> None:
        tabla = TablaExtraidaDTO(encabezados=("ColumnaX", "ColumnaY"), filas=[{"ColumnaX": "a", "ColumnaY": "b"}])
        assert normalizar_tabla(tabla, _reglas()) == []

    def test_fila_sin_nombre_se_descarta(self) -> None:
        tabla = TablaExtraidaDTO(encabezados=("Cargo",), filas=[{"Cargo": "Director"}])
        assert normalizar_tabla(tabla, _reglas()) == []

    def test_columnas_faltantes_quedan_vacias_sin_error(self) -> None:
        tabla = TablaExtraidaDTO(encabezados=("Nombres",), filas=[{"Nombres": "Juan"}])
        resultado = normalizar_tabla(tabla, _reglas())
        assert resultado[0].cargo == ""
        assert resultado[0].dependencia == ""
        assert resultado[0].correo is None

    def test_tabla_vacia(self) -> None:
        tabla = TablaExtraidaDTO(encabezados=(), filas=[])
        assert normalizar_tabla(tabla, _reglas()) == []

    def test_tolera_variacion_de_encabezado(self) -> None:
        """'Puesto' y 'Unidad' son sinonimos de cargo/dependencia -- no
        hace falta el texto exacto."""
        tabla = TablaExtraidaDTO(
            encabezados=("Nombres", "Apellidos", "Puesto", "Unidad"),
            filas=[{"Nombres": "Ana", "Apellidos": "Lopez", "Puesto": "Abogada", "Unidad": "Legal"}],
        )
        resultado = normalizar_tabla(tabla, _reglas())
        assert resultado[0].cargo == "Abogada"
        assert resultado[0].dependencia == "Legal"


class TestLimpiarExtensionTelefonica:
    @pytest.mark.parametrize(
        ("valor", "esperado"),
        [
            ("103", "103"),
            (" 1045 ", "1045"),
            ("Ext. 101", "101"),
            ("EXTENSIÓN 2201", "2201"),
            ("101 / 102", "101 / 102"),
            ("101, 102 y 103", "101, 102 y 103"),
            ("103.0", "103"),
            ('NO APLICA DEBIDO A "Que no posse extensión en su oficina"', None),
            ("N/A", None),
            ("-", None),
            ("", None),
            (None, None),
            ("1" * 25, None),
        ],
    )
    def test_solo_acepta_valores_con_forma_de_extension(self, valor, esperado) -> None:
        assert limpiar_extension_telefonica(valor) == esperado

    def test_normalizar_tabla_descarta_texto_no_aplica(self) -> None:
        reglas = ReglasNormalizacion(
            sinonimos_por_campo={"nombres": ["Nombres"], "extension_telefonica": ["Extension telefonica"]}
        )
        tabla = TablaExtraidaDTO(
            encabezados=("Nombres", "Extension telefonica"),
            filas=[{"Nombres": "Ana", "Extension telefonica": "NO APLICA"}, {"Nombres": "Luis", "Extension telefonica": "101"}],
        )
        filas = normalizar_tabla(tabla, reglas)
        assert [f.extension_telefonica for f in filas] == [None, "101"]


class TestLimpiarTelefono:
    @pytest.mark.parametrize(
        ("valor", "esperado"),
        [
            ("(07) 2647-117\n(07) 2647-118", "(07) 2647-117"),
            ("(04) 2768 099\n(04) 2768030", "(04) 2768 099"),
            ("022 345 678 / 022 345 679", "022 345 678"),
            ("0991234567", "0991234567"),
            ("N/A", "N/A"),
            ("", None),
            (None, None),
        ],
    )
    def test_toma_el_primer_numero_valido(self, valor, esperado) -> None:
        assert limpiar_telefono(valor) == esperado
