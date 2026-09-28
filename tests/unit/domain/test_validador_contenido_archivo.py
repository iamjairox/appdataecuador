"""Tests: validador de contenido real (Content-Type -> Magic Bytes -> Extension)."""

from __future__ import annotations

from pathlib import Path

import pytest

from govdata.domain.entities.documento import TipoArchivo
from govdata.domain.rules.validador_contenido_archivo import (
    detectar_por_content_type,
    detectar_por_magic_bytes,
    es_pagina_error_html,
    mime_por_tipo,
    resolver_tipo_real,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "documentos"


def _bytes(nombre: str) -> bytes:
    return (FIXTURES / nombre).read_bytes()


class TestDetectarPorMagicBytes:
    def test_pdf(self) -> None:
        assert detectar_por_magic_bytes(_bytes("directorio_valido.pdf")) == TipoArchivo.PDF

    def test_xlsx(self) -> None:
        assert detectar_por_magic_bytes(_bytes("directorio_valido.xlsx")) == TipoArchivo.XLSX

    def test_xls(self) -> None:
        assert detectar_por_magic_bytes(_bytes("directorio_valido.xls")) == TipoArchivo.XLS

    def test_csv_no_tiene_firma_propia(self) -> None:
        assert detectar_por_magic_bytes(_bytes("directorio_valido.csv")) is None

    def test_html_no_es_ningun_tipo_soportado(self) -> None:
        assert detectar_por_magic_bytes(_bytes("pagina_error_disfrazada.pdf")) is None

    def test_corrupto_sin_firma(self) -> None:
        assert detectar_por_magic_bytes(_bytes("archivo_corrupto.bin")) is None

    def test_vacio(self) -> None:
        assert detectar_por_magic_bytes(b"") is None


class TestDetectarPorContentType:
    def test_pdf(self) -> None:
        assert detectar_por_content_type("application/pdf") == TipoArchivo.PDF

    def test_con_charset(self) -> None:
        assert detectar_por_content_type("text/csv; charset=utf-8") == TipoArchivo.CSV

    def test_desconocido(self) -> None:
        assert detectar_por_content_type("application/octet-stream") is None

    def test_none(self) -> None:
        assert detectar_por_content_type(None) is None


class TestEsPaginaErrorHtml:
    def test_por_content_type(self) -> None:
        assert es_pagina_error_html("text/html; charset=utf-8", b"cualquier cosa") is True

    def test_por_firma_html_sin_content_type_declarado(self) -> None:
        assert es_pagina_error_html(None, _bytes("pagina_error_disfrazada.pdf")) is True

    def test_pdf_real_no_es_pagina_error(self) -> None:
        assert es_pagina_error_html("application/pdf", _bytes("directorio_valido.pdf")) is False

    def test_csv_real_no_es_pagina_error(self) -> None:
        assert es_pagina_error_html("text/csv", _bytes("directorio_valido.csv")) is False


class TestResolverTipoReal:
    def test_pdf_real_con_content_type_correcto(self) -> None:
        resultado = resolver_tipo_real("application/pdf", _bytes("directorio_valido.pdf"), TipoArchivo.PDF)
        assert resultado.tipo_detectado == TipoArchivo.PDF
        assert resultado.fuente == "magic-bytes"
        assert resultado.coincide_con_esperado is True

    def test_caso_central_pdf_falso_es_html(self) -> None:
        """El caso que motiva el modulo: Content-Type dice PDF, pero los
        bytes reales son una pagina de error HTML -- magic bytes manda."""
        resultado = resolver_tipo_real(
            "application/pdf", _bytes("pagina_error_disfrazada.pdf"), TipoArchivo.PDF
        )
        assert resultado.tipo_detectado is None
        assert resultado.fuente == "ninguna"
        assert resultado.coincide_con_esperado is False

    def test_magic_bytes_manda_sobre_content_type_incorrecto(self) -> None:
        """Content-Type dice CSV pero los bytes son un PDF real -- se
        confia en los bytes, no en lo que declaro el servidor."""
        resultado = resolver_tipo_real("text/csv", _bytes("directorio_valido.pdf"), TipoArchivo.CSV)
        assert resultado.tipo_detectado == TipoArchivo.PDF
        assert resultado.fuente == "magic-bytes"
        assert resultado.coincide_con_esperado is False

    def test_xlsx_real(self) -> None:
        resultado = resolver_tipo_real(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            _bytes("directorio_valido.xlsx"),
            TipoArchivo.XLSX,
        )
        assert resultado.tipo_detectado == TipoArchivo.XLSX
        assert resultado.coincide_con_esperado is True

    def test_csv_se_acepta_por_descarte(self) -> None:
        resultado = resolver_tipo_real(None, _bytes("directorio_valido.csv"), TipoArchivo.CSV)
        assert resultado.tipo_detectado == TipoArchivo.CSV
        assert resultado.fuente == "extension"
        assert resultado.coincide_con_esperado is True

    def test_csv_esperado_pero_es_pagina_de_error(self) -> None:
        resultado = resolver_tipo_real(
            "text/html", _bytes("pagina_error_disfrazada.pdf"), TipoArchivo.CSV
        )
        assert resultado.tipo_detectado is None

    def test_archivo_corrupto_sin_ninguna_senal(self) -> None:
        resultado = resolver_tipo_real(None, _bytes("archivo_corrupto.bin"), TipoArchivo.PDF)
        assert resultado.tipo_detectado is None
        assert resultado.fuente == "ninguna"

    @pytest.mark.parametrize(
        "tipo",
        [TipoArchivo.PDF, TipoArchivo.XLS, TipoArchivo.XLSX, TipoArchivo.CSV],
    )
    def test_mime_por_tipo_cubre_todos_los_tipos(self, tipo: TipoArchivo) -> None:
        assert mime_por_tipo(tipo)
