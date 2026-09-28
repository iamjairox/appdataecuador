"""Tests: PriorizacionService (Submodulo 6.11)."""

from __future__ import annotations

from govdata.application.services.priorizacion_service import PriorizacionService
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.rules.reglas_identidad import ReglasPriorizacion
from govdata.domain.value_objects.nombre_completo import NombreCompleto

_REGLAS = ReglasPriorizacion(
    prioridad_por_cargo={"Director Juridico": 100.0, "Abogado": 80.0},
    prioridad_defecto=10.0,
    umbral_score_minimo=80.0,
)


def _pm(id_: int) -> PersonaMaster:
    return PersonaMaster(persona_id=id_, nombre_completo=NombreCompleto("Juan", "Perez"), id=id_)


class TestPriorizar:
    def test_ordena_candidatas_por_cargo_de_mayor_a_menor_prioridad(self) -> None:
        servicio = PriorizacionService(_REGLAS)
        p1, p2, p3 = _pm(1), _pm(2), _pm(3)
        cargos = {1: "Abogado", 2: "Director Juridico", 3: "Chofer"}
        resultado = servicio.priorizar([p1, p2, p3], cargos)
        assert [p.id for p in resultado] == [2, 1, 3]

    def test_persona_master_sin_cargo_conocido_usa_prioridad_defecto(self) -> None:
        servicio = PriorizacionService(_REGLAS)
        p1 = _pm(1)
        resultado = servicio.priorizar([p1], {})
        assert resultado == [p1]
