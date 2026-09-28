"""Tests: ProgramadorEnriquecimientoService (Submodulo 7.20, mejora 2)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from govdata.application.services.priorizacion_service import PriorizacionService
from govdata.application.services.programador_enriquecimiento_service import (
    ProgramadorEnriquecimientoService,
)
from govdata.domain.entities.alerta_academica import AlertaAcademica
from govdata.domain.entities.consulta_senescyt import ConsultaSenescyt
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.rules.reglas_identidad import ReglasPriorizacion
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.tipo_alerta_academica import TipoAlertaAcademica
from tests.unit.application.fakes_modulo6 import FakePersonaMasterRepository
from tests.unit.application.fakes_modulo7 import (
    FakeAlertaAcademicaRepository,
    FakeConsultaSenescytRepository,
)

_AHORA = datetime(2026, 6, 1, tzinfo=UTC)


def _pm(id_: int) -> PersonaMaster:
    return PersonaMaster(persona_id=id_, nombre_completo=NombreCompleto("Juan", f"Perez{id_}"))


def _servicio():
    from govdata.domain.rules.reglas_academicas import ReglasCacheSenescyt

    pm_repo = FakePersonaMasterRepository()
    consulta_repo = FakeConsultaSenescytRepository()
    alerta_repo = FakeAlertaAcademicaRepository()
    priorizacion = PriorizacionService(ReglasPriorizacion(prioridad_por_cargo={}, prioridad_defecto=10.0))
    servicio = ProgramadorEnriquecimientoService(
        pm_repo, consulta_repo, alerta_repo, priorizacion, ReglasCacheSenescyt(dias_vigencia=30)
    )
    return servicio, pm_repo, consulta_repo, alerta_repo


class TestDebeReenriquecerseAhora:
    def test_sin_consultas_previas_debe_reenriquecerse(self) -> None:
        servicio, *_ = _servicio()
        assert servicio.debe_reenriquecerse_ahora(1, _AHORA) is True

    def test_consulta_reciente_no_debe_reenriquecerse(self) -> None:
        servicio, _pm_repo, consulta_repo, _alerta_repo = _servicio()
        consulta = ConsultaSenescyt(persona_master_id=1, iniciado_en=_AHORA - timedelta(days=5))
        consulta.finalizar(exito=True, cuando=_AHORA - timedelta(days=5), duracion_segundos=1.0)
        consulta_repo.guardar(consulta)
        assert servicio.debe_reenriquecerse_ahora(1, _AHORA) is False

    def test_consulta_vencida_debe_reenriquecerse(self) -> None:
        servicio, _pm_repo, consulta_repo, _alerta_repo = _servicio()
        consulta = ConsultaSenescyt(persona_master_id=1, iniciado_en=_AHORA - timedelta(days=40))
        consulta.finalizar(exito=True, cuando=_AHORA - timedelta(days=40), duracion_segundos=1.0)
        consulta_repo.guardar(consulta)
        assert servicio.debe_reenriquecerse_ahora(1, _AHORA) is True


class TestCandidatosAEnriquecer:
    def test_personas_con_alerta_pendiente_van_primero(self) -> None:
        servicio, pm_repo, _consulta_repo, alerta_repo = _servicio()
        pm1 = pm_repo.guardar(_pm(1))
        pm2 = pm_repo.guardar(_pm(2))
        alerta_repo.guardar(
            AlertaAcademica(
                persona_master_id=pm2.id, tipo=TipoAlertaAcademica.NUEVO_TITULO, prioridad=NivelCriticidad.MEDIO,
                descripcion="x", detectado_en=_AHORA,
            )
        )
        candidatos = servicio.candidatos_a_enriquecer(_AHORA)
        assert candidatos[0].id == pm2.id
        assert pm1.id in [c.id for c in candidatos]

    def test_persona_con_cache_vigente_no_es_candidata(self) -> None:
        servicio, pm_repo, consulta_repo, _alerta_repo = _servicio()
        pm1 = pm_repo.guardar(_pm(1))
        consulta = ConsultaSenescyt(persona_master_id=pm1.id, iniciado_en=_AHORA - timedelta(days=1))
        consulta.finalizar(exito=True, cuando=_AHORA - timedelta(days=1), duracion_segundos=1.0)
        consulta_repo.guardar(consulta)

        candidatos = servicio.candidatos_a_enriquecer(_AHORA)
        assert candidatos == []
