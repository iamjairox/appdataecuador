"""Tests: DescubrirDocumentoUseCase."""

from __future__ import annotations

from datetime import date

import pytest

from govdata.application.dto.descubrimiento_dto import ArchivoDTO, NumeralPublicadoDTO
from govdata.application.use_cases.descubrir_documento_use_case import DescubrirDocumentoUseCase
from govdata.domain.entities.documento import TipoArchivo
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.publicacion import PublicacionMensual
from govdata.domain.exceptions.domain_exceptions import DocumentoNoSoportadoError
from tests.unit.application.fakes import FakeDocumentoRepository, FakePortalScraperPort


def _entidad() -> Entidad:
    return Entidad(
        id=1, nombre="Entidad X", url_transparencia="https://x/entidades/1", portal_origen="dpe"
    )


def _publicacion() -> PublicacionMensual:
    return PublicacionMensual(
        id=1, entidad_id=1, mes_publicado=date(2026, 6, 1), url_item="https://x/entidades/1?anio=2026&mes=6"
    )


def test_encuentra_y_persiste_el_documento() -> None:
    numerales = [
        NumeralPublicadoDTO(descripcion="Estructura orgánica"),
        NumeralPublicadoDTO(
            descripcion="Directorio y distributivo personal de la entidad",
            archivos=[
                ArchivoDTO(descripcion="Metadatos", nombre="m.csv", url_descarga="/m.csv"),
                ArchivoDTO(descripcion="Conjunto de datos", nombre="directorio.csv", url_descarga="/directorio.csv"),
            ],
        ),
    ]
    scraper = FakePortalScraperPort(numerales_por_mes={(2026, 6): numerales})
    repo = FakeDocumentoRepository()

    documento = DescubrirDocumentoUseCase(scraper, repo).ejecutar(_entidad(), _publicacion())

    assert documento.tipo_archivo == TipoArchivo.CSV
    assert documento.nombre_original == "directorio.csv"
    assert documento.url_documento == "/directorio.csv"
    assert documento.esta_descargado is False
    assert len(repo.guardados) == 1


def test_sin_numeral_directorio_lanza_error() -> None:
    numerales = [NumeralPublicadoDTO(descripcion="Presupuesto de la institucion")]
    scraper = FakePortalScraperPort(numerales_por_mes={(2026, 6): numerales})

    with pytest.raises(DocumentoNoSoportadoError):
        DescubrirDocumentoUseCase(scraper, FakeDocumentoRepository()).ejecutar(_entidad(), _publicacion())


def test_numeral_encontrado_sin_archivo_de_datos_lanza_error() -> None:
    numerales = [
        NumeralPublicadoDTO(
            descripcion="Directorio y distributivo del personal",
            archivos=[ArchivoDTO(descripcion="Metadatos", nombre="m.csv", url_descarga="/m.csv")],
        )
    ]
    scraper = FakePortalScraperPort(numerales_por_mes={(2026, 6): numerales})

    with pytest.raises(DocumentoNoSoportadoError):
        DescubrirDocumentoUseCase(scraper, FakeDocumentoRepository()).ejecutar(_entidad(), _publicacion())


def test_tipo_de_archivo_no_reconocido_lanza_error() -> None:
    numerales = [
        NumeralPublicadoDTO(
            descripcion="Directorio y distributivo del personal",
            archivos=[
                ArchivoDTO(descripcion="Conjunto de datos", nombre="d.docx", url_descarga="/d.docx")
            ],
        )
    ]
    scraper = FakePortalScraperPort(numerales_por_mes={(2026, 6): numerales})

    with pytest.raises(DocumentoNoSoportadoError):
        DescubrirDocumentoUseCase(scraper, FakeDocumentoRepository()).ejecutar(_entidad(), _publicacion())


def test_detecta_pdf_correctamente() -> None:
    numerales = [
        NumeralPublicadoDTO(
            descripcion="Directorio del personal",
            archivos=[
                ArchivoDTO(descripcion="Conjunto de datos", nombre="d.pdf", url_descarga="/d.pdf")
            ],
        )
    ]
    scraper = FakePortalScraperPort(numerales_por_mes={(2026, 6): numerales})
    documento = DescubrirDocumentoUseCase(scraper, FakeDocumentoRepository()).ejecutar(
        _entidad(), _publicacion()
    )
    assert documento.tipo_archivo == TipoArchivo.PDF


def test_publicacion_sin_id_lanza_error() -> None:
    scraper = FakePortalScraperPort()
    publicacion_sin_id = PublicacionMensual(
        entidad_id=1, mes_publicado=date(2026, 6, 1), url_item="https://x/1?anio=2026&mes=6"
    )
    with pytest.raises(DocumentoNoSoportadoError):
        DescubrirDocumentoUseCase(scraper, FakeDocumentoRepository()).ejecutar(
            _entidad(), publicacion_sin_id
        )
