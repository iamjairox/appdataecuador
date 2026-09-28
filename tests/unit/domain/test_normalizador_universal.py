"""Tests: Normalizador Universal (Submodulo 4.2)."""

from __future__ import annotations

from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO
from govdata.domain.rules.normalizador_universal import dividir_nombre_completo, normalizar_tabla
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
