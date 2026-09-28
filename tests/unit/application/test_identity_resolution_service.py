"""Tests: IdentityResolutionService (Submodulo 6.2, orquestacion)."""

from __future__ import annotations

from govdata.application.services.identity_resolution_service import IdentityResolutionService
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.rules.reglas_identidad import PesosScoring
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes_modulo6 import FakePersonaMasterRepository

_PESOS = PesosScoring(
    fingerprint=0.40, correo=0.25, nombre=0.15, apellido=0.10, institucion=0.05, cargo=0.05,
    umbral_minimo_coincidencia=60.0,
)


def _pm(fingerprint: str, correo: str | None = None) -> PersonaMaster:
    return PersonaMaster(
        persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"), fingerprint_principal=fingerprint,
        correo_principal=Correo(correo) if correo else None,
    )


class TestBuscarCandidatas:
    def test_acota_por_fingerprint_exacto(self) -> None:
        repo = FakePersonaMasterRepository()
        repo.guardar(_pm("FP1"))
        repo.guardar(_pm("FP2"))
        servicio = IdentityResolutionService(repo, _PESOS)

        from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO

        senales = SenalesIdentidadDTO(nombre="Juan", apellido="Perez", fingerprint="FP1")
        candidatas = servicio.buscar_candidatas(senales)
        assert len(candidatas) == 1
        assert candidatas[0][0] == 1

    def test_deduplica_candidatas_encontradas_por_multiples_vias(self) -> None:
        repo = FakePersonaMasterRepository()
        repo.guardar(_pm("FP1", correo="fijo@x.com"))
        servicio = IdentityResolutionService(repo, _PESOS)

        from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO

        senales = SenalesIdentidadDTO(nombre="Juan", apellido="Perez", fingerprint="FP1", correo="fijo@x.com")
        candidatas = servicio.buscar_candidatas(senales)
        assert len(candidatas) == 1

    def test_sin_senales_no_produce_candidatas(self) -> None:
        repo = FakePersonaMasterRepository()
        repo.guardar(_pm("FP1"))
        servicio = IdentityResolutionService(repo, _PESOS)

        from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO

        senales = SenalesIdentidadDTO(nombre="Juan", apellido="Perez")
        assert servicio.buscar_candidatas(senales) == []


class TestResolver:
    def test_resuelve_contra_candidata_identica(self) -> None:
        repo = FakePersonaMasterRepository()
        repo.guardar(_pm("FP1"))
        servicio = IdentityResolutionService(repo, _PESOS)

        from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO

        senales = SenalesIdentidadDTO(nombre="Juan", apellido="Perez", fingerprint="FP1")
        resultado = servicio.resolver(senales)
        assert resultado.persona_master_id == 1
