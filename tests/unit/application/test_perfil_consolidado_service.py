"""Tests: PerfilConsolidadoService -- Submodulo 8.10."""

from __future__ import annotations

import pytest

from govdata.application.services.perfil_academico_service import PerfilAcademicoService
from govdata.application.services.perfil_consolidado_service import PerfilConsolidadoService
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.persona import Persona
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.entities.registro_foro import RegistroForo
from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.cargo import Cargo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes import FakeEntidadRepository
from tests.unit.application.fakes_extraccion import (
    FakeFuncionarioRepositoryExtraccion,
    FakePersonaRepository,
)
from tests.unit.application.fakes_modulo6 import FakePersonaMasterRepository
from tests.unit.application.fakes_modulo7 import (
    FakeAlertaAcademicaRepository,
    FakeEventoAcademicoRepository,
    FakeHistorialAcademicoRepository,
    FakeTituloAcademicoRepository,
)
from tests.unit.application.fakes_modulo8 import (
    FakeAlertaForoRepository,
    FakeEventoForoRepository,
    FakeHistorialForoRepository,
    FakeRegistroForoRepository,
)


def _construir_servicio():
    pm_repo = FakePersonaMasterRepository()
    persona_repo = FakePersonaRepository()
    funcionario_repo = FakeFuncionarioRepositoryExtraccion()
    entidad_repo = FakeEntidadRepository()
    perfil_academico_service = PerfilAcademicoService(
        pm_repo, FakeTituloAcademicoRepository(), FakeHistorialAcademicoRepository(),
        FakeEventoAcademicoRepository(), FakeAlertaAcademicaRepository(),
    )
    registro_foro_repo = FakeRegistroForoRepository()
    historial_foro_repo = FakeHistorialForoRepository()
    evento_foro_repo = FakeEventoForoRepository()
    alerta_foro_repo = FakeAlertaForoRepository()

    servicio = PerfilConsolidadoService(
        pm_repo, persona_repo, funcionario_repo, entidad_repo, perfil_academico_service, registro_foro_repo,
        historial_foro_repo, evento_foro_repo, alerta_foro_repo,
    )
    return servicio, pm_repo, persona_repo, funcionario_repo, entidad_repo, registro_foro_repo


class TestConstruirPerfil:
    def test_persona_master_inexistente_lanza_error(self) -> None:
        servicio, *_ = _construir_servicio()
        with pytest.raises(PersonaMasterInvalidaError):
            servicio.construir_perfil(999)

    def test_construye_las_4_claves_del_contrato(self) -> None:
        servicio, pm_repo, persona_repo, _funcionario_repo, _entidad_repo, _registro_repo = _construir_servicio()
        persona = persona_repo.guardar(Persona(nombre_completo=NombreCompleto("Juan", "Perez"), cedula="0999999999"))
        pm = pm_repo.guardar(PersonaMaster(persona_id=persona.id, nombre_completo=NombreCompleto("Juan", "Perez")))

        perfil = servicio.construir_perfil(pm.id)

        assert perfil.persona["cedula"] == "0999999999"
        assert perfil.transparencia == {"cargos": []}
        assert "titulos" in perfil.senescyt
        assert "registros" in perfil.foro

    def test_transparencia_con_entidad_id_incluye_el_cargo_vigente(self) -> None:
        servicio, pm_repo, persona_repo, funcionario_repo, entidad_repo, _registro_repo = _construir_servicio()
        persona = persona_repo.guardar(Persona(nombre_completo=NombreCompleto("Juan", "Perez")))
        pm = pm_repo.guardar(PersonaMaster(persona_id=persona.id, nombre_completo=NombreCompleto("Juan", "Perez")))
        entidad = entidad_repo.guardar_o_actualizar(
            Entidad(nombre="Procuraduria", url_transparencia="https://x.test", portal_origen="dpe")
        )
        funcionario_repo.guardar(
            Funcionario(
                persona_id=persona.id, entidad_id=entidad.id, cargo=Cargo("Director Juridico"),
                dependencia="Direccion Juridica", area_clasificada=AreaRelevante.JURIDICA,
            )
        )

        perfil = servicio.construir_perfil(pm.id, entidad_id=entidad.id)
        assert len(perfil.transparencia["cargos"]) == 1
        assert perfil.transparencia["cargos"][0]["entidad"] == "Procuraduria"

    def test_foro_incluye_registros_vigentes(self) -> None:
        servicio, pm_repo, persona_repo, _funcionario_repo, _entidad_repo, registro_repo = _construir_servicio()
        persona = persona_repo.guardar(Persona(nombre_completo=NombreCompleto("Juan", "Perez")))
        pm = pm_repo.guardar(PersonaMaster(persona_id=persona.id, nombre_completo=NombreCompleto("Juan", "Perez")))
        registro_repo.guardar(RegistroForo(persona_master_id=pm.id, clave_registro="r1", registro="R1"))

        perfil = servicio.construir_perfil(pm.id)
        assert len(perfil.foro["registros"]) == 1
