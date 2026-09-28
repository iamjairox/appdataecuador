"""Tests: DescubrirUltimaPublicacionUseCase."""

from __future__ import annotations

from datetime import date

import pytest

from govdata.application.use_cases.descubrir_ultima_publicacion_use_case import (
    DescubrirUltimaPublicacionUseCase,
)
from govdata.domain.entities.entidad import Entidad
from govdata.domain.exceptions.domain_exceptions import PublicacionNoDisponibleError
from tests.unit.application.fakes import FakePortalScraperPort, FakePublicacionRepository


def _entidad(id_: int = 1) -> Entidad:
    return Entidad(
        id=id_, nombre="Entidad X", url_transparencia="https://x/entidades/1", portal_origen="dpe"
    )


def test_detecta_el_mes_mas_reciente_del_anio_actual() -> None:
    scraper = FakePortalScraperPort(meses_por_anio={2026: [1, 2, 6]})
    caso_uso = DescubrirUltimaPublicacionUseCase(
        scraper, FakePublicacionRepository(), anio_actual_provider=lambda: 2026
    )
    publicacion = caso_uso.ejecutar(_entidad())

    assert publicacion.mes_publicado == date(2026, 6, 1)
    assert publicacion.entidad_id == 1


def test_retrocede_al_anio_anterior_si_el_actual_esta_vacio() -> None:
    scraper = FakePortalScraperPort(meses_por_anio={2026: [], 2025: [11]})
    caso_uso = DescubrirUltimaPublicacionUseCase(
        scraper, FakePublicacionRepository(), anio_actual_provider=lambda: 2026
    )
    publicacion = caso_uso.ejecutar(_entidad())

    assert publicacion.mes_publicado == date(2025, 11, 1)
    # Debe haber consultado 2026 antes que 2025 (orden descendente correcto).
    assert scraper.llamadas_meses == [
        ("https://x/entidades/1", 2026),
        ("https://x/entidades/1", 2025),
    ]


def test_no_reintenta_mas_alla_del_lookback_configurado() -> None:
    scraper = FakePortalScraperPort(meses_por_anio={})
    caso_uso = DescubrirUltimaPublicacionUseCase(
        scraper,
        FakePublicacionRepository(),
        anios_lookback_maximo=2,
        anio_actual_provider=lambda: 2026,
    )
    with pytest.raises(PublicacionNoDisponibleError):
        caso_uso.ejecutar(_entidad())

    # anio actual + 2 anios hacia atras = 3 llamadas (2026, 2025, 2024)
    assert len(scraper.llamadas_meses) == 3


def test_persiste_la_publicacion_detectada() -> None:
    scraper = FakePortalScraperPort(meses_por_anio={2026: [6]})
    repo = FakePublicacionRepository()
    caso_uso = DescubrirUltimaPublicacionUseCase(scraper, repo, anio_actual_provider=lambda: 2026)
    caso_uso.ejecutar(_entidad())

    assert len(repo.guardadas) == 1
    assert repo.guardadas[0].id is not None


def test_entidad_sin_id_lanza_error() -> None:
    scraper = FakePortalScraperPort(meses_por_anio={2026: [6]})
    caso_uso = DescubrirUltimaPublicacionUseCase(
        scraper, FakePublicacionRepository(), anio_actual_provider=lambda: 2026
    )
    with pytest.raises(PublicacionNoDisponibleError):
        caso_uso.ejecutar(_entidad(id_=None))  # type: ignore[arg-type]
