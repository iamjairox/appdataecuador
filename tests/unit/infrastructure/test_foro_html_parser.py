"""Tests: parsear_registro_foro -- Submodulo 8.4 (Parser HTML)."""

from __future__ import annotations

from govdata.domain.rules.reglas_foro import CatalogoCamposForo
from govdata.infrastructure.http.foro_html_parser import parsear_registro_foro

_CATALOGO = CatalogoCamposForo(
    campo_por_etiqueta={
        "NO REGISTRO": "registro", "PROVINCIA": "provincia", "ESTADO": "estado",
        "NOMBRE COMPLETO": "nombre_completo", "CEDULA": "cedula",
    }
)


class TestParsearRegistroForoTablas:
    def test_extrae_campos_de_una_tabla_html(self) -> None:
        html = """
        <table>
            <tr><td>No. Registro</td><td>R-12345</td></tr>
            <tr><td>Provincia</td><td>Pichincha</td></tr>
            <tr><td>Estado</td><td>Vigente</td></tr>
        </table>
        """
        registro = parsear_registro_foro(html, _CATALOGO)
        assert registro is not None
        assert registro.registro == "R-12345"
        assert registro.provincia == "Pichincha"
        assert registro.estado == "Vigente"

    def test_columnas_desconocidas_se_ignoran_sin_fallar(self) -> None:
        html = "<table><tr><td>Direccion</td><td>Av. Siempre Viva</td></tr></table>"
        assert parsear_registro_foro(html, _CATALOGO) is None


class TestParsearRegistroForoParesSueltos:
    def test_extrae_campos_de_strong_labels(self) -> None:
        html = """
        <div>
            <p><strong>Nombre Completo:</strong> Juan Perez</p>
            <p><strong>Provincia:</strong> Guayas</p>
        </div>
        """
        registro = parsear_registro_foro(html, _CATALOGO)
        assert registro is not None
        assert registro.nombre_completo == "Juan Perez"
        assert registro.provincia == "Guayas"

    def test_forma_mixta_tabla_y_pares_sueltos(self) -> None:
        html = """
        <table><tr><td>No. Registro</td><td>R-1</td></tr></table>
        <p><strong>Estado:</strong> Suspendido</p>
        """
        registro = parsear_registro_foro(html, _CATALOGO)
        assert registro is not None
        assert registro.registro == "R-1"
        assert registro.estado == "Suspendido"


class TestParsearRegistroForoSinDatos:
    def test_html_sin_ningun_campo_reconocido_retorna_none(self) -> None:
        assert parsear_registro_foro("<html><body>Sin resultados</body></html>", _CATALOGO) is None
