"""Tests: ResolverOCrearPersonaMasterUseCase -- UNICO punto de alta de
PersonaMaster (Submodulos 6.1 + 6.2 + 6.21). Garantiza "nunca personas
duplicadas"."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from govdata.application.services.fusion_service import FusionService
from govdata.application.services.identity_resolution_service import IdentityResolutionService
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError
from govdata.domain.rules.reglas_identidad import UmbralesFusion
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.estado_persona_master import EstadoPersonaMaster
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes_modulo6 import (
    FakeCasoRevisionIdentidadRepository,
    FakeEventoPerfilRepository,
    FakePersonaMasterRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _caso_uso():
    from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad

    reglas = cargar_rule_engine_identidad()
    pm_repo = FakePersonaMasterRepository()
    caso_repo = FakeCasoRevisionIdentidadRepository()
    evento_repo = FakeEventoPerfilRepository()

    identity_service = IdentityResolutionService(pm_repo, reglas.scoring)
    fusion_service = FusionService(
        pm_repo, caso_repo, evento_repo, UmbralesFusion(98.0, 85.0), ahora_provider=lambda: _AHORA
    )
    caso_uso = ResolverOCrearPersonaMasterUseCase(pm_repo, identity_service, fusion_service, ahora_provider=lambda: _AHORA)
    return caso_uso, pm_repo


def _persona(id_: int, nombres: str = "Juan", apellidos: str = "Perez", correo: str | None = None, fingerprint: str | None = None) -> Persona:
    return Persona(
        id=id_, nombre_completo=NombreCompleto(nombres, apellidos), correo=Correo(correo) if correo else None,
        fingerprint=fingerprint,
    )


class TestEjecutar:
    def test_persona_sin_id_falla(self) -> None:
        caso_uso, _ = _caso_uso()
        persona_sin_id = Persona(id=None, nombre_completo=NombreCompleto("Juan", "Perez"))
        with pytest.raises(PersonaMasterInvalidaError):
            caso_uso.ejecutar(persona_sin_id)

    def test_primera_vez_crea_persona_master_nueva(self) -> None:
        caso_uso, pm_repo = _caso_uso()
        persona = _persona(1, fingerprint="AAA")
        pm = caso_uso.ejecutar(persona)
        assert pm.persona_id == 1
        assert pm.estado == EstadoPersonaMaster.ACTIVA
        assert len(pm_repo.guardadas) == 1

    def test_idempotente_no_duplica_si_ya_existe_persona_master(self) -> None:
        caso_uso, pm_repo = _caso_uso()
        persona = _persona(1, fingerprint="AAA")
        pm1 = caso_uso.ejecutar(persona)
        pm2 = caso_uso.ejecutar(persona)
        assert pm1.id == pm2.id
        assert len(pm_repo.guardadas) == 1  # NUNCA una segunda

    def test_fingerprint_y_correo_identicos_sin_mas_contexto_va_a_revision_manual(self) -> None:
        """`PersonaMaster` (a diferencia de `Persona`/`Funcionario`) no
        almacena institucion/cargo -- solo se conocen del lado NUEVO (los
        pasa el llamador), nunca del lado de una candidata ya persistida.
        Con solo 4 de las 6 senales de la especificacion con evidencia
        real (fingerprint 40% + correo 25% + nombre 15% + apellido 10% =
        90% de techo posible), el score NUNCA alcanza automaticamente el
        umbral de fusion automatica (98%) sin una fuente adicional que
        aporte institucion/cargo del lado de la candidata -- limitacion
        documentada (ver informe final), no un error: el sistema prefiere
        pedir revision manual antes que arriesgar un falso positivo."""
        caso_uso, pm_repo = _caso_uso()
        persona_1 = _persona(1, fingerprint="JUANPEREZ", correo="fijo@x.com")
        persona_2 = _persona(2, fingerprint="JUANPEREZ", correo="fijo@x.com")

        pm1 = caso_uso.ejecutar(persona_1, cargo="Director Juridico", institucion="DPE")
        pm2 = caso_uso.ejecutar(persona_2, cargo="Director Juridico", institucion="DPE")

        assert pm1.id != pm2.id  # NO se fusiono automaticamente
        assert pm2.estado == EstadoPersonaMaster.EN_REVISION
        activas = [p for p in pm_repo.guardadas if p.estado != EstadoPersonaMaster.FUSIONADA]
        assert len(activas) == 2  # ambas siguen existiendo hasta que alguien revise el caso

    def test_solo_fingerprint_y_correo_sin_institucion_ni_cargo_va_a_revision_manual(self) -> None:
        """Con solo 2 de las 6 senales con evidencia (fingerprint+correo),
        el score maximo alcanzable (90%) cae en la zona de revision manual
        (85-97.99%) -- el sistema NUNCA fusiona automaticamente sin mas
        contexto, aunque fingerprint y correo coincidan exactamente."""
        caso_uso, _pm_repo = _caso_uso()
        persona_1 = _persona(1, fingerprint="JUANPEREZ", correo="fijo@x.com")
        persona_2 = _persona(2, fingerprint="JUANPEREZ", correo="fijo@x.com")

        pm1 = caso_uso.ejecutar(persona_1)
        pm2 = caso_uso.ejecutar(persona_2)

        assert pm1.id != pm2.id  # NO se fusiono automaticamente
        assert pm2.estado == EstadoPersonaMaster.EN_REVISION

    def test_personas_genuinamente_distintas_nunca_se_fusionan(self) -> None:
        caso_uso, pm_repo = _caso_uso()
        persona_1 = _persona(1, nombres="Juan", apellidos="Perez", fingerprint="JUANPEREZ", correo="juan@x.com")
        persona_2 = _persona(2, nombres="Maria", apellidos="Lopez", fingerprint="MARIALOPEZ", correo="maria@y.com")

        pm1 = caso_uso.ejecutar(persona_1)
        pm2 = caso_uso.ejecutar(persona_2)

        assert pm1.id != pm2.id
        activas = [p for p in pm_repo.guardadas if p.estado != EstadoPersonaMaster.FUSIONADA]
        assert len(activas) == 2
