"""Tests: deteccion de fila de encabezado y hoja (Submodulo 4.1)."""

from __future__ import annotations

from govdata.domain.rules.detector_encabezado import (
    detectar_fila_encabezado,
    encabezados_unicos,
    limpiar_celda_encabezado,
    seleccionar_hoja_y_encabezado,
)
from govdata.domain.rules.reglas_configurables import ReglasNormalizacion

_SINONIMOS = {
    "nombre_completo": ["Apellidos y Nombres", "Nombres y Apellidos", "Servidor"],
    "cargo": ["Cargo", "Puesto", "Puesto Institucional"],
    "dependencia": ["Unidad", "Unidad a la que pertenece"],
    "correo": ["Correo", "Correo electronico institucional"],
}
_REGLAS = ReglasNormalizacion(sinonimos_por_campo=_SINONIMOS)
_ENCABEZADO = ["No.", "Apellidos y Nombres", "Puesto Institucional", "Unidad a la que pertenece", "Correo"]
_DATO = ["1", "PEREZ GOMEZ JUAN CARLOS", "ANALISTA JURIDICO 1", "DIRECCION DE ASESORIA JURIDICA", "juan@x.gob.ec"]


class TestDetectarFilaEncabezado:
    def test_encabezado_en_la_primera_fila(self) -> None:
        deteccion = detectar_fila_encabezado([_ENCABEZADO, _DATO], _REGLAS)
        assert deteccion.indice_fila == 0
        assert deteccion.reconocidos == 4

    def test_encabezado_en_la_cuarta_fila_tras_titulos_y_filas_vacias(self) -> None:
        filas = [
            ["GOBIERNO AUTONOMO DESCENTRALIZADO MUNICIPAL DEL CANTON EJEMPLO", None, None, None, None],
            [None, None, None, None, None],
            ["Literal 2 - Directorio y distributivo personal de la entidad", "", "", "", ""],
            _ENCABEZADO,
            _DATO,
        ]
        assert detectar_fila_encabezado(filas, _REGLAS).indice_fila == 3

    def test_encabezado_multilinea(self) -> None:
        filas = [["Titulo"], ["No.", "Apellidos y\nNombres", "Puesto\nInstitucional", "Unidad a la\nque pertenece"]]
        assert detectar_fila_encabezado(filas, _REGLAS).indice_fila == 1

    def test_sin_ninguna_fila_reconocible_conserva_la_primera(self) -> None:
        filas = [["a", "b"], ["c", "d"]]
        assert detectar_fila_encabezado(filas, _REGLAS).indice_fila == 0

    def test_una_fila_de_datos_no_se_confunde_con_encabezado(self) -> None:
        filas = [_DATO, _ENCABEZADO, _DATO]
        assert detectar_fila_encabezado(filas, _REGLAS).indice_fila == 1

    def test_sin_filas(self) -> None:
        assert detectar_fila_encabezado([], _REGLAS).indice_fila == 0


class TestSeleccionarHoja:
    def test_hoja_incorrecta_primero(self) -> None:
        portada = [["Portada"], ["Institucion: Ejemplo"], ["Fecha de corte: 2026"]]
        distributivo = [["Titulo"], _ENCABEZADO, _DATO]
        deteccion = seleccionar_hoja_y_encabezado([portada, distributivo], _REGLAS)
        assert (deteccion.indice_hoja, deteccion.indice_fila) == (1, 1)

    def test_empate_gana_la_primera_hoja(self) -> None:
        deteccion = seleccionar_hoja_y_encabezado([[_ENCABEZADO], [_ENCABEZADO]], _REGLAS)
        assert deteccion.indice_hoja == 0

    def test_sin_hojas(self) -> None:
        assert seleccionar_hoja_y_encabezado([], _REGLAS).indice_hoja == 0


class TestUtilidades:
    def test_limpiar_celda_colapsa_saltos_de_linea(self) -> None:
        assert limpiar_celda_encabezado(" Apellidos y\nNombres  ") == "Apellidos y Nombres"
        assert limpiar_celda_encabezado(None) == ""

    def test_columnas_duplicadas_no_se_pisan(self) -> None:
        assert encabezados_unicos(["Correo", "Cargo", "Correo", "", ""]) == ("Correo", "Cargo", "Correo (2)", "", "")
