"""Tests: DescubrirEntidadUseCase (garantia de 'nunca detener el pipeline')."""

from __future__ import annotations

from datetime import date

from govdata.application.use_cases.descubrir_documento_use_case import DescubrirDocumentoUseCase
from govdata.application.use_cases.descubrir_entidad_use_case import DescubrirEntidadUseCase
from govdata.application.use_cases.descubrir_ultima_publicacion_use_case import (
    DescubrirUltimaPublicacionUseCase,
)
from govdata.domain.entities.entidad import Entidad
from govdata.domain.exceptions.domain_exceptions import EntidadNoEncontradaError
from tests.unit.application.fakes import (
    FakeDocumentoRepository,
    FakePortalScraperPort,
    FakePublicacionRepository,
)


def _entidad() -> Entidad:
    return Entidad(
        id=1, nombre="Entidad Rota", url_transparencia="https://x/entidades/1", portal_origen="dpe"
    )


def test_publicacion_no_disponible_no_propaga_excepcion() -> None:
    """Entidad sin Transparencia Activa / sin publicaciones: resultado con
    exito=False, la excepcion NUNCA sale de este caso de uso."""
    scraper = FakePortalScraperPort(meses_por_anio={})  # ningun anio tiene publicaciones
    descubrir_pub = DescubrirUltimaPublicacionUseCase(
        scraper, FakePublicacionRepository(), anios_lookback_maximo=1, anio_actual_provider=lambda: 2026
    )
    descubrir_doc = DescubrirDocumentoUseCase(scraper, FakeDocumentoRepository())

    resultado = DescubrirEntidadUseCase(descubrir_pub, descubrir_doc).ejecutar(_entidad())

    assert resultado.exito is False
    assert resultado.publicacion is None
    assert resultado.documento is None
    assert resultado.error is not None


def test_error_de_red_en_publicacion_no_propaga_excepcion() -> None:
    """Simula timeout/pagina inexistente al listar meses -- debe capturarse."""
    scraper = FakePortalScraperPort(error_a_lanzar=EntidadNoEncontradaError("404"))
    descubrir_pub = DescubrirUltimaPublicacionUseCase(
        scraper, FakePublicacionRepository(), anios_lookback_maximo=0, anio_actual_provider=lambda: 2026
    )
    descubrir_doc = DescubrirDocumentoUseCase(scraper, FakeDocumentoRepository())

    resultado = DescubrirEntidadUseCase(descubrir_pub, descubrir_doc).ejecutar(_entidad())

    assert resultado.exito is False
    assert resultado.documento is None


def test_documento_no_encontrado_no_propaga_excepcion() -> None:
    """La publicacion SI se encuentra, pero el documento no -- resultado
    parcial: exito=False, pero publicacion poblada."""
    scraper = FakePortalScraperPort(
        meses_por_anio={2026: [6]},
        numerales_por_mes={(2026, 6): []},  # sin numerales -> no se encuentra el item
    )
    descubrir_pub = DescubrirUltimaPublicacionUseCase(
        scraper, FakePublicacionRepository(), anio_actual_provider=lambda: 2026
    )
    descubrir_doc = DescubrirDocumentoUseCase(scraper, FakeDocumentoRepository())

    resultado = DescubrirEntidadUseCase(descubrir_pub, descubrir_doc).ejecutar(_entidad())

    assert resultado.exito is False
    assert resultado.publicacion is not None
    assert resultado.documento is None


def test_flujo_completo_exitoso() -> None:
    from govdata.application.dto.descubrimiento_dto import ArchivoDTO, NumeralPublicadoDTO

    scraper = FakePortalScraperPort(
        meses_por_anio={2026: [6]},
        numerales_por_mes={
            (2026, 6): [
                NumeralPublicadoDTO(
                    descripcion="Directorio y distributivo del personal",
                    archivos=[
                        ArchivoDTO(descripcion="Conjunto de datos", nombre="d.csv", url_descarga="/d.csv")
                    ],
                )
            ]
        },
    )
    descubrir_pub = DescubrirUltimaPublicacionUseCase(
        scraper, FakePublicacionRepository(), anio_actual_provider=lambda: 2026
    )
    descubrir_doc = DescubrirDocumentoUseCase(scraper, FakeDocumentoRepository())

    resultado = DescubrirEntidadUseCase(descubrir_pub, descubrir_doc).ejecutar(_entidad())

    assert resultado.exito is True
    assert resultado.publicacion is not None
    assert resultado.publicacion.mes_publicado == date(2026, 6, 1)
    assert resultado.documento is not None
    assert resultado.error is None
