"""Tests: ListarEntidadesUseCase."""

from __future__ import annotations

from govdata.application.dto.entidad_dto import EntidadDescubiertaDTO
from govdata.application.use_cases.listar_entidades_use_case import ListarEntidadesUseCase
from tests.unit.application.fakes import FakeEntidadRepository, FakePortalScraperPort


def test_persiste_todas_las_entidades_descubiertas() -> None:
    scraper = FakePortalScraperPort(
        entidades=[
            EntidadDescubiertaDTO(nombre="A", url_transparencia="https://x/1", portal_origen="dpe"),
            EntidadDescubiertaDTO(nombre="B", url_transparencia="https://x/2", portal_origen="dpe"),
        ]
    )
    repo = FakeEntidadRepository()
    resultado = ListarEntidadesUseCase(scraper, repo).ejecutar()

    assert len(resultado) == 2
    assert all(e.id is not None for e in resultado)


def test_no_duplica_si_ya_existe_por_url() -> None:
    scraper = FakePortalScraperPort(
        entidades=[
            EntidadDescubiertaDTO(nombre="A", url_transparencia="https://x/1", portal_origen="dpe"),
        ]
    )
    repo = FakeEntidadRepository()
    ListarEntidadesUseCase(scraper, repo).ejecutar()
    ListarEntidadesUseCase(scraper, repo).ejecutar()

    assert len(repo.guardadas) == 1


def test_actualiza_nombre_si_cambio() -> None:
    repo = FakeEntidadRepository()
    scraper_v1 = FakePortalScraperPort(
        entidades=[EntidadDescubiertaDTO(nombre="Nombre Viejo", url_transparencia="https://x/1", portal_origen="dpe")]
    )
    ListarEntidadesUseCase(scraper_v1, repo).ejecutar()

    scraper_v2 = FakePortalScraperPort(
        entidades=[EntidadDescubiertaDTO(nombre="Nombre Nuevo", url_transparencia="https://x/1", portal_origen="dpe")]
    )
    resultado = ListarEntidadesUseCase(scraper_v2, repo).ejecutar()

    assert len(repo.guardadas) == 1
    assert resultado[0].nombre == "Nombre Nuevo"


def test_guarda_metadata_extra_del_portal() -> None:
    scraper = FakePortalScraperPort(
        entidades=[
            EntidadDescubiertaDTO(
                nombre="A",
                url_transparencia="https://x/1",
                portal_origen="dpe",
                identificador_portal="123",
                tipo_institucion="FUNCION EJECUTIVA",
            )
        ]
    )
    repo = FakeEntidadRepository()
    resultado = ListarEntidadesUseCase(scraper, repo).ejecutar()

    assert resultado[0].metadata_extra["identificador_portal"] == "123"
    assert resultado[0].metadata_extra["tipo_institucion"] == "FUNCION EJECUTIVA"
