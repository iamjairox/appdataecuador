"""Tests de integracion: parsers REALES (Submodulo 4.1) contra las
fixtures binarias reales de `tests/fixtures/extraccion/` -- sin fakes,
sin mocks. Complementa `tests/unit/application/test_parser_factory.py`
(que usa un `DocumentParserPort` fake) verificando que camelot,
pdfplumber, openpyxl, xlrd y `csv.Sniffer` de verdad producen el DTO
esperado contra archivos reales.
"""

from __future__ import annotations

from pathlib import Path

from govdata.application.dto.resultado_parseo_dto import EstadoParseo
from govdata.application.services.parser_factory import ParserFactory
from govdata.domain.entities.documento import TipoArchivo
from govdata.infrastructure.parsers.csv.csv_parser import CsvParser
from govdata.infrastructure.parsers.excel.xls_parser import XlsParser
from govdata.infrastructure.parsers.excel.xlsx_parser import XlsxParser
from govdata.infrastructure.parsers.pdf.pdf_parser_engine import PdfParserEngine

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "extraccion"


def _factory() -> ParserFactory:
    return ParserFactory([PdfParserEngine(), XlsxParser(), XlsParser(), CsvParser()])


class TestPdfReal:
    def test_pdf_con_tabla_via_camelot(self) -> None:
        resultado = PdfParserEngine().extraer(str(FIXTURES / "directorio_con_tabla.pdf"))
        assert resultado.estado == EstadoParseo.EXITO
        assert resultado.tabla is not None
        assert resultado.tabla.cantidad_filas == 5
        assert len(resultado.tabla.encabezados) >= 2

    def test_pdf_con_texto_via_fallback_pdfplumber(self) -> None:
        resultado = PdfParserEngine().extraer(str(FIXTURES / "directorio_con_texto.pdf"))
        assert resultado.estado == EstadoParseo.EXITO
        assert resultado.tabla is not None
        assert resultado.tabla.cantidad_filas >= 1

    def test_pdf_escaneado_requiere_ocr(self) -> None:
        resultado = PdfParserEngine().extraer(str(FIXTURES / "directorio_escaneado.pdf"))
        assert resultado.estado == EstadoParseo.REQUIERE_OCR

    def test_pdf_vacio_no_falla_el_pipeline(self) -> None:
        resultado = PdfParserEngine().extraer(str(FIXTURES / "pdf_vacio.pdf"))
        assert resultado.estado in (EstadoParseo.EXITO, EstadoParseo.REQUIERE_OCR)

    def test_pdf_corrupto_produce_error_controlado(self) -> None:
        resultado = PdfParserEngine().extraer(str(FIXTURES / "corrupto.pdf"))
        assert resultado.estado == EstadoParseo.ERROR
        assert resultado.mensaje


class TestXlsxReal:
    def test_directorio_con_encabezados_variados(self) -> None:
        resultado = XlsxParser().extraer(str(FIXTURES / "directorio.xlsx"))
        assert resultado.estado == EstadoParseo.EXITO
        assert resultado.tabla is not None
        # 5 filas de datos; la fila en blanco intercalada debe filtrarse.
        assert resultado.tabla.cantidad_filas == 5
        assert "Servidor" in resultado.tabla.encabezados

    def test_columnas_desconocidas_se_extraen_tal_cual(self) -> None:
        """El parser NO sabe de sinonimos -- eso es responsabilidad del
        Normalizador (4.2). El parser solo debe devolver la fila cruda."""
        resultado = XlsxParser().extraer(str(FIXTURES / "columnas_desconocidas.xlsx"))
        assert resultado.estado == EstadoParseo.EXITO
        assert resultado.tabla is not None
        assert resultado.tabla.encabezados == ("ColumnaX", "ColumnaY", "ColumnaZ")

    def test_excel_vacio(self) -> None:
        resultado = XlsxParser().extraer(str(FIXTURES / "excel_vacio.xlsx"))
        assert resultado.estado == EstadoParseo.EXITO
        assert resultado.tabla is not None
        assert resultado.tabla.cantidad_filas == 0

    def test_xlsx_corrupto_produce_error_controlado(self) -> None:
        resultado = XlsxParser().extraer(str(FIXTURES / "corrupto.xlsx"))
        assert resultado.estado == EstadoParseo.ERROR


class TestXlsReal:
    def test_xls_legado_incompleto_produce_error_controlado(self) -> None:
        """Solo la firma OLE, sin contenido real -- `xlrd` debe rechazarlo
        con un error controlado, nunca una excepcion sin capturar."""
        resultado = XlsParser().extraer(str(FIXTURES / "legado_incompleto.xls"))
        assert resultado.estado == EstadoParseo.ERROR


class TestCsvReal:
    def test_csv_delimitado_por_punto_y_coma_con_encabezado_combinado(self) -> None:
        resultado = CsvParser().extraer(str(FIXTURES / "directorio.csv"))
        assert resultado.estado == EstadoParseo.EXITO
        assert resultado.tabla is not None
        assert resultado.tabla.cantidad_filas == 5
        assert "Nombres y Apellidos" in resultado.tabla.encabezados

    def test_csv_vacio(self) -> None:
        resultado = CsvParser().extraer(str(FIXTURES / "csv_vacio.csv"))
        assert resultado.estado == EstadoParseo.EXITO
        assert resultado.tabla is not None
        assert resultado.tabla.cantidad_filas == 0

    def test_csv_corrupto_produce_error_controlado(self) -> None:
        resultado = CsvParser().extraer(str(FIXTURES / "corrupto.csv"))
        assert resultado.estado == EstadoParseo.ERROR


class TestParserFactoryConArchivosReales:
    def test_selecciona_el_parser_correcto_por_extension(self) -> None:
        factory = _factory()
        assert isinstance(factory.obtener_parser(TipoArchivo.PDF), PdfParserEngine)
        assert isinstance(factory.obtener_parser(TipoArchivo.XLSX), XlsxParser)
        assert isinstance(factory.obtener_parser(TipoArchivo.XLS), XlsParser)
        assert isinstance(factory.obtener_parser(TipoArchivo.CSV), CsvParser)
