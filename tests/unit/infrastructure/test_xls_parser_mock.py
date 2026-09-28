"""Tests: `XlsParser` con `xlrd.open_workbook` mockeado.

No existe una libreria pura-Python para GENERAR un `.xls` real valido
bajo Python 3.13 (`xlwt` no lo soporta -- ver
`tests/fixtures/extraccion/_generar.py`), asi que el camino "exitoso" del
parser (que SI requiere un workbook `xlrd` real y bien formado) se cubre
aqui simulando el objeto que `xlrd.open_workbook(...).sheet_by_index(0)`
devolveria. El camino de error (archivo corrupto) SI se cubre con un
archivo real en `tests/integration/test_parsers_reales.py`
(`legado_incompleto.xls`)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from govdata.application.dto.resultado_parseo_dto import EstadoParseo
from govdata.infrastructure.parsers.excel.xls_parser import XlsParser


def _hoja_fake(filas: list[list[object]]) -> MagicMock:
    hoja = MagicMock()
    hoja.nrows = len(filas)
    hoja.row_values.side_effect = lambda indice: filas[indice]
    return hoja


class TestXlsParserExtraccionExitosa:
    def test_extrae_encabezados_y_filas_omitiendo_filas_en_blanco(self) -> None:
        filas_crudas = [
            ["Nombre Completo", "Cargo", "Dependencia"],
            ["Juan Perez", "Director Juridico", "Legal"],
            ["", "", ""],  # fila en blanco -- debe omitirse
            ["Ana Lopez", "Asesora Juridica", "Legal"],
        ]
        hoja = _hoja_fake(filas_crudas)
        libro = MagicMock()
        libro.sheet_by_index.return_value = hoja

        with patch("govdata.infrastructure.parsers.excel.xls_parser.xlrd.open_workbook", return_value=libro):
            resultado = XlsParser().extraer("cualquier-ruta.xls")

        assert resultado.estado == EstadoParseo.EXITO
        assert resultado.tabla is not None
        assert resultado.tabla.encabezados == ("Nombre Completo", "Cargo", "Dependencia")
        assert resultado.tabla.cantidad_filas == 2
        assert resultado.tabla.filas[0]["Nombre Completo"] == "Juan Perez"

    def test_hoja_vacia_produce_tabla_vacia_sin_error(self) -> None:
        hoja = _hoja_fake([])
        libro = MagicMock()
        libro.sheet_by_index.return_value = hoja

        with patch("govdata.infrastructure.parsers.excel.xls_parser.xlrd.open_workbook", return_value=libro):
            resultado = XlsParser().extraer("vacio.xls")

        assert resultado.estado == EstadoParseo.EXITO
        assert resultado.tabla is not None
        assert resultado.tabla.cantidad_filas == 0
        assert resultado.mensaje == "Excel vacio"


class TestXlsParserErrores:
    def test_apertura_fallida_produce_error_controlado(self) -> None:
        with patch(
            "govdata.infrastructure.parsers.excel.xls_parser.xlrd.open_workbook",
            side_effect=Exception("archivo corrupto"),
        ):
            resultado = XlsParser().extraer("corrupto.xls")

        assert resultado.estado == EstadoParseo.ERROR
        assert resultado.mensaje is not None
        assert "corrupto" in resultado.mensaje


def test_soporta_solo_xls() -> None:
    from govdata.domain.entities.documento import TipoArchivo

    parser = XlsParser()
    assert parser.soporta(TipoArchivo.XLS) is True
    assert parser.soporta(TipoArchivo.XLSX) is False
