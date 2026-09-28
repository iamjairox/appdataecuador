"""Tests: TimelinePersonaService (Submodulo 6.5) -- reutiliza
`HistorialService` (Modulo 5) sin reimplementar el historial institucional."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from govdata.application.services.historial_service import HistorialService
from govdata.application.services.timeline_persona_service import TimelinePersonaService
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.entities.registro_fuente import RegistroFuente
from govdata.domain.entities.version_funcionario import EstadoVersion, VersionFuncionario
from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes_modulo5 import FakeVersionFuncionarioRepository
from tests.unit.application.fakes_modulo6 import FakeRegistroFuenteRepository


def _pm() -> PersonaMaster:
    return PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"), id=1)


class TestConstruirTimeline:
    def test_requiere_persona_master_persistida(self) -> None:
        version_repo = FakeVersionFuncionarioRepository()
        registro_repo = FakeRegistroFuenteRepository()
        servicio = TimelinePersonaService(HistorialService(version_repo), registro_repo)
        pm_sin_id = PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"))
        with pytest.raises(PersonaMasterInvalidaError):
            servicio.construir(pm_sin_id)

    def test_combina_historial_institucional_y_registros_de_fuente(self) -> None:
        version_repo = FakeVersionFuncionarioRepository()
        version_repo.guardar(
            VersionFuncionario(
                persona_id=1, entidad_id=1, numero_version=1, cargo="Asesor Juridico", dependencia="Legal",
                area="juridica", documento_id=1, fecha_inicio=date(2019, 1, 1), fecha_fin=date(2021, 1, 1),
                estado=EstadoVersion.CERRADA,
            )
        )
        version_repo.guardar(
            VersionFuncionario(
                persona_id=1, entidad_id=1, numero_version=2, cargo="Director Juridico", dependencia="Legal",
                area="juridica", documento_id=2, fecha_inicio=date(2023, 1, 1),
            )
        )
        registro_repo = FakeRegistroFuenteRepository()
        registro_repo.guardar(
            RegistroFuente(
                persona_master_id=1, fuente=FuenteExterna.SENESCYT, version=1, datos={"titulo": "Abogado"},
                consultado_en=datetime(2020, 6, 1, tzinfo=UTC),
            )
        )

        servicio = TimelinePersonaService(HistorialService(version_repo), registro_repo)
        timeline = servicio.construir(_pm())

        assert timeline.persona_master_id == 1
        assert len(timeline.puntos) == 3
        # ordenado cronologicamente: 2019 (institucional) -> 2020 (senescyt) -> 2023 (institucional)
        assert timeline.puntos[0].origen == "institucional"
        assert timeline.puntos[1].origen == "senescyt"
        assert timeline.puntos[2].descripcion.startswith("Director Juridico")

    def test_sin_historial_produce_timeline_vacio(self) -> None:
        servicio = TimelinePersonaService(
            HistorialService(FakeVersionFuncionarioRepository()), FakeRegistroFuenteRepository()
        )
        timeline = servicio.construir(_pm())
        assert timeline.puntos == []
