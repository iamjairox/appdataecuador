"""Tests: FusionService (Submodulos 6.14 + 6.21)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from govdata.application.dto.identity_resolution_result_dto import IdentityResolutionResultDTO
from govdata.application.services.fusion_service import FusionService
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.rules.reglas_identidad import UmbralesFusion
from govdata.domain.value_objects.decision_fusion import DecisionFusion
from govdata.domain.value_objects.estado_persona_master import EstadoPersonaMaster
from govdata.domain.value_objects.estado_revision_identidad import EstadoRevisionIdentidad
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes_modulo6 import (
    FakeCasoRevisionIdentidadRepository,
    FakeEventoPerfilRepository,
    FakePersonaMasterRepository,
)

_UMBRALES = UmbralesFusion(umbral_fusion_automatica=98.0, umbral_revision_manual=85.0)
_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _pm() -> PersonaMaster:
    return PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"))


def _resultado(persona_master_id: int | None, score: float) -> IdentityResolutionResultDTO:
    return IdentityResolutionResultDTO(
        persona_master_id=persona_master_id, score=score, nivel_confianza="alta", explicacion="x",
        motivo="mejor_candidata_seleccionada", campos_utilizados=[],
    )


def _servicio() -> tuple[FusionService, FakePersonaMasterRepository, FakeCasoRevisionIdentidadRepository, FakeEventoPerfilRepository]:
    persona_master_repo = FakePersonaMasterRepository()
    caso_repo = FakeCasoRevisionIdentidadRepository()
    evento_repo = FakeEventoPerfilRepository()
    servicio = FusionService(persona_master_repo, caso_repo, evento_repo, _UMBRALES, ahora_provider=lambda: _AHORA)
    return servicio, persona_master_repo, caso_repo, evento_repo


class TestEvaluarYDecidirFusionAutomatica:
    def test_score_alto_sin_persona_master_id_identificada_falla(self) -> None:
        """Defensivo: un `IdentityResolutionResultDTO` con score de fusion
        automatica pero sin `persona_master_id` (nunca deberia ocurrir en
        la practica -- `resolver_identidad` siempre limpia el
        persona_master_id cuando no hay coincidencia) debe fallar en vez
        de fusionar a ciegas."""
        from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError

        servicio, _repo, _caso_repo, _evento_repo = _servicio()
        nueva = PersonaMaster(persona_id=2, nombre_completo=NombreCompleto("Juan", "Perez"))
        with pytest.raises(PersonaMasterInvalidaError):
            servicio.evaluar_y_decidir(nueva, _resultado(None, 99.0))

    def test_score_98_fusiona_automaticamente(self) -> None:
        servicio, repo, caso_repo, evento_repo = _servicio()
        ganadora = repo.guardar(_pm())

        nueva = PersonaMaster(persona_id=2, nombre_completo=NombreCompleto("Juan", "Perez"))
        decision = servicio.evaluar_y_decidir(nueva, _resultado(ganadora.id, 98.5))

        assert decision.decision == DecisionFusion.FUSION_AUTOMATICA
        assert decision.persona_master_resultante_id == ganadora.id
        assert nueva.estado == EstadoPersonaMaster.FUSIONADA
        assert nueva.fusionada_en_id == ganadora.id
        assert ganadora.cantidad_fuentes == 2  # incrementado por la fusion
        assert len(evento_repo.guardados) == 1

        caso = caso_repo.guardados[0]
        assert caso.estado == EstadoRevisionIdentidad.APROBADO
        assert caso.resuelto_por is not None and "sistema" in caso.resuelto_por


class TestEvaluarYDecidirRevisionManual:
    def test_score_90_crea_caso_pendiente_sin_fusionar(self) -> None:
        servicio, repo, caso_repo, evento_repo = _servicio()
        candidata = repo.guardar(_pm())

        nueva = PersonaMaster(persona_id=2, nombre_completo=NombreCompleto("Juan", "Perez"))
        decision = servicio.evaluar_y_decidir(nueva, _resultado(candidata.id, 90.0))

        assert decision.decision == DecisionFusion.REVISION_MANUAL
        assert nueva.estado == EstadoPersonaMaster.EN_REVISION
        assert nueva.id is not None  # se guardo, no se descarto
        assert candidata.estado == EstadoPersonaMaster.ACTIVA  # nunca se toca sin decision humana
        assert len(caso_repo.guardados) == 1
        assert caso_repo.guardados[0].estado == EstadoRevisionIdentidad.PENDIENTE_REVISION
        assert evento_repo.guardados == []  # ningun evento hasta que se resuelva


class TestEvaluarYDecidirMantenerSeparadas:
    def test_score_bajo_guarda_como_identidad_nueva_independiente(self) -> None:
        servicio, _repo, caso_repo, evento_repo = _servicio()

        nueva = PersonaMaster(persona_id=2, nombre_completo=NombreCompleto("Maria", "Lopez"))
        decision = servicio.evaluar_y_decidir(nueva, _resultado(None, 20.0))

        assert decision.decision == DecisionFusion.MANTENER_SEPARADAS
        assert nueva.estado == EstadoPersonaMaster.ACTIVA
        assert caso_repo.guardados == []
        assert evento_repo.guardados == []


class TestRevisarCaso:
    def test_aprobar_ejecuta_fusion_real(self) -> None:
        servicio, repo, caso_repo, evento_repo = _servicio()
        ganadora = repo.guardar(_pm())
        candidata = repo.guardar(PersonaMaster(persona_id=2, nombre_completo=NombreCompleto("Juan", "Perez")))
        candidata.marcar_en_revision()
        repo.guardar(candidata)

        from govdata.domain.entities.caso_revision_identidad import CasoRevisionIdentidad

        caso = caso_repo.guardar(
            CasoRevisionIdentidad(
                persona_master_id_a=ganadora.id, persona_master_id_b=candidata.id, score=90.0,
                explicacion="x", campos_utilizados=("correo",), creado_en=_AHORA,
            )
        )

        resultado = servicio.revisar_caso(caso.uuid, aprobar=True, revisor="ana.revisora", cuando=_AHORA)
        assert resultado.estado == EstadoRevisionIdentidad.APROBADO
        assert candidata.estado == EstadoPersonaMaster.FUSIONADA
        assert candidata.fusionada_en_id == ganadora.id
        assert ganadora.estado == EstadoPersonaMaster.ACTIVA
        assert len(evento_repo.guardados) == 1

    def test_rechazar_reactiva_la_candidata_sin_fusionar(self) -> None:
        servicio, repo, caso_repo, evento_repo = _servicio()
        ganadora = repo.guardar(_pm())
        candidata = repo.guardar(PersonaMaster(persona_id=2, nombre_completo=NombreCompleto("Juan", "Perez")))
        candidata.marcar_en_revision()
        repo.guardar(candidata)

        from govdata.domain.entities.caso_revision_identidad import CasoRevisionIdentidad

        caso = caso_repo.guardar(
            CasoRevisionIdentidad(
                persona_master_id_a=ganadora.id, persona_master_id_b=candidata.id, score=90.0,
                explicacion="x", campos_utilizados=(), creado_en=_AHORA,
            )
        )

        resultado = servicio.revisar_caso(caso.uuid, aprobar=False, revisor="ana.revisora", cuando=_AHORA)
        assert resultado.estado == EstadoRevisionIdentidad.RECHAZADO
        assert candidata.estado == EstadoPersonaMaster.ACTIVA
        assert evento_repo.guardados == []

    def test_caso_inexistente_falla(self) -> None:
        import uuid

        from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError

        servicio, *_ = _servicio()
        with pytest.raises(PersonaMasterInvalidaError):
            servicio.revisar_caso(uuid.uuid4(), aprobar=True, revisor="ana", cuando=_AHORA)

    def test_aprobar_caso_sin_persona_master_id_b_no_ejecuta_fusion(self) -> None:
        """Un caso originado por una fuente externa (`registro_fuente_id`,
        sin `persona_master_id_b`) puede aprobarse (queda auditado) sin
        que haya una segunda PersonaMaster que fusionar."""
        servicio, repo, caso_repo, evento_repo = _servicio()
        ganadora = repo.guardar(_pm())

        from govdata.domain.entities.caso_revision_identidad import CasoRevisionIdentidad

        caso = caso_repo.guardar(
            CasoRevisionIdentidad(
                persona_master_id_a=ganadora.id, registro_fuente_id=99, score=90.0, explicacion="x",
                campos_utilizados=(), creado_en=_AHORA,
            )
        )
        resultado = servicio.revisar_caso(caso.uuid, aprobar=True, revisor="ana", cuando=_AHORA)
        assert resultado.estado == EstadoRevisionIdentidad.APROBADO
        assert evento_repo.guardados == []

    def test_ganadora_o_perdedora_inexistente_en_fusion_manual_falla(self) -> None:
        from govdata.domain.entities.caso_revision_identidad import CasoRevisionIdentidad
        from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError

        servicio, repo, caso_repo, _evento_repo = _servicio()
        ganadora = repo.guardar(_pm())
        caso = caso_repo.guardar(
            CasoRevisionIdentidad(
                persona_master_id_a=ganadora.id, persona_master_id_b=99999, score=90.0, explicacion="x",
                campos_utilizados=(), creado_en=_AHORA,
            )
        )
        with pytest.raises(PersonaMasterInvalidaError):
            servicio.revisar_caso(caso.uuid, aprobar=True, revisor="ana", cuando=_AHORA)
