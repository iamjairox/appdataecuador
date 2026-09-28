"""Tests: RegistroFuenteService (Submodulo 6.9 + 6.15)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.services.registro_fuente_service import RegistroFuenteService
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from tests.unit.application.fakes_modulo6 import (
    FakeAtributoTrazableRepository,
    FakeRegistroFuenteRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _servicio() -> tuple[RegistroFuenteService, FakeRegistroFuenteRepository, FakeAtributoTrazableRepository]:
    registro_repo = FakeRegistroFuenteRepository()
    atributo_repo = FakeAtributoTrazableRepository()
    return RegistroFuenteService(registro_repo, atributo_repo), registro_repo, atributo_repo


class TestRegistrarRespuesta:
    def test_primera_version_no_tiene_cambios_anteriores(self) -> None:
        servicio, _registro_repo, atributo_repo = _servicio()
        registro, cambios = servicio.registrar_respuesta(
            1, FuenteExterna.SENESCYT, {"titulo": "Abogado"}, _AHORA
        )
        assert registro.version == 1
        assert registro.vigente
        assert cambios == {"titulo": (None, "Abogado")}
        assert len(atributo_repo.guardados) == 1

    def test_segunda_version_cierra_la_anterior_y_reporta_diferencias(self) -> None:
        servicio, registro_repo, _ = _servicio()
        servicio.registrar_respuesta(1, FuenteExterna.SENESCYT, {"titulo": "Abogado"}, _AHORA)
        registro_2, cambios = servicio.registrar_respuesta(
            1, FuenteExterna.SENESCYT, {"titulo": "Doctor en Jurisprudencia"}, _AHORA
        )
        assert registro_2.version == 2
        assert cambios == {"titulo": ("Abogado", "Doctor en Jurisprudencia")}

        anteriores = [r for r in registro_repo.guardados if r.version == 1]
        assert len(anteriores) == 1
        assert not anteriores[0].vigente  # nunca se sobreescribe, solo se cierra

    def test_sin_cambios_reales_produce_diccionario_vacio(self) -> None:
        servicio, _, _ = _servicio()
        servicio.registrar_respuesta(1, FuenteExterna.SENESCYT, {"titulo": "Abogado"}, _AHORA)
        _, cambios = servicio.registrar_respuesta(1, FuenteExterna.SENESCYT, {"titulo": "Abogado"}, _AHORA)
        assert cambios == {}

    def test_hash_contenido_se_calcula(self) -> None:
        servicio, _, _ = _servicio()
        registro, _ = servicio.registrar_respuesta(1, FuenteExterna.SENESCYT, {"titulo": "Abogado"}, _AHORA)
        assert registro.hash_contenido is not None
        assert len(registro.hash_contenido) == 64

    def test_atributos_trazables_registran_fuente_y_score(self) -> None:
        servicio, _, atributo_repo = _servicio()
        servicio.registrar_respuesta(1, FuenteExterna.SENESCYT, {"titulo": "Abogado"}, _AHORA, score_confianza=80.0)
        atributo = atributo_repo.guardados[0]
        assert atributo.fuente == FuenteExterna.SENESCYT
        assert atributo.score == 80.0
        assert atributo.valor == "Abogado"
