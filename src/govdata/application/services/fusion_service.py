"""Servicio: FusionService -- Submodulo 6.14 (Motor de Fusion) + 6.21
(Motor de Confianza y Revision Manual, sugerencia del cliente).

Unico lugar que ejecuta una fusion real de `PersonaMaster` o crea un caso
de revision manual. Nunca fusiona automaticamente por debajo del umbral
de alta confianza -- toda decision (automatica o manual) queda auditada
en un `CasoRevisionIdentidad`, incluida la propia fusion automatica (con
`resuelto_por="sistema:auto"`), para que "quien o que la tomo, cuando y
con que criterio" siempre se pueda responder.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from govdata.application.dto.decision_fusion_dto import DecisionFusionDTO
from govdata.application.dto.identity_resolution_result_dto import IdentityResolutionResultDTO
from govdata.application.ports.caso_revision_identidad_repository_port import (
    CasoRevisionIdentidadRepositoryPort,
)
from govdata.application.ports.evento_perfil_repository_port import EventoPerfilRepositoryPort
from govdata.application.ports.persona_master_repository_port import PersonaMasterRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.caso_revision_identidad import CasoRevisionIdentidad
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError
from govdata.domain.rules.generador_eventos_perfil import generar_evento_persona_fusionada
from govdata.domain.rules.motor_confianza_fusion import decidir_fusion
from govdata.domain.rules.reglas_identidad import UmbralesFusion
from govdata.domain.value_objects.decision_fusion import DecisionFusion

logger = get_logger(__name__)


class FusionService:
    def __init__(
        self,
        persona_master_repository: PersonaMasterRepositoryPort,
        caso_revision_repository: CasoRevisionIdentidadRepositoryPort,
        evento_perfil_repository: EventoPerfilRepositoryPort,
        umbrales: UmbralesFusion,
        ahora_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._persona_master_repository = persona_master_repository
        self._caso_revision_repository = caso_revision_repository
        self._evento_perfil_repository = evento_perfil_repository
        self._umbrales = umbrales
        self._ahora_provider = ahora_provider

    def evaluar_y_decidir(
        self,
        persona_master_nueva: PersonaMaster,
        resultado: IdentityResolutionResultDTO,
        decidido_por: str = "sistema",
    ) -> DecisionFusionDTO:
        """`persona_master_nueva` todavia NO esta persistida. Segun el
        score de `resultado`: fusiona automaticamente con la candidata
        (>= umbral_fusion_automatica), crea un caso de revision manual sin
        fusionar (umbral_revision_manual..umbral_fusion_automatica), o la
        guarda como una identidad nueva e independiente (< umbral_revision_manual)."""
        decision = decidir_fusion(resultado.score, self._umbrales)
        cuando = self._ahora_provider()
        campos_utilizados = tuple(c.campo for c in resultado.campos_utilizados if c.peso > 0)

        if decision == DecisionFusion.FUSION_AUTOMATICA:
            return self._fusionar_automaticamente(persona_master_nueva, resultado, campos_utilizados, cuando)

        if decision == DecisionFusion.REVISION_MANUAL:
            return self._crear_caso_revision(persona_master_nueva, resultado, campos_utilizados, cuando)

        guardada = self._persona_master_repository.guardar(persona_master_nueva)
        logger.info("identidad_mantenida_separada", persona_master_id=guardada.id, score=resultado.score)
        return DecisionFusionDTO(
            decision=decision,
            score=resultado.score,
            persona_master_resultante_id=self._id_no_none(guardada),
            explicacion=resultado.explicacion,
        )

    def _fusionar_automaticamente(
        self,
        persona_master_nueva: PersonaMaster,
        resultado: IdentityResolutionResultDTO,
        campos_utilizados: tuple[str, ...],
        cuando: datetime,
    ) -> DecisionFusionDTO:
        if resultado.persona_master_id is None:
            raise PersonaMasterInvalidaError("Fusion automatica requiere una candidata identificada")
        ganadora = self._persona_master_repository.buscar_por_id(resultado.persona_master_id)
        if ganadora is None or ganadora.id is None:
            raise PersonaMasterInvalidaError(
                f"PersonaMaster candidata no encontrada: {resultado.persona_master_id}"
            )

        persona_master_nueva.fusionar_en(ganadora.id)
        absorbida = self._persona_master_repository.guardar(persona_master_nueva)
        ganadora.registrar_nueva_fuente()
        ganadora_guardada = self._persona_master_repository.guardar(ganadora)

        caso = CasoRevisionIdentidad(
            persona_master_id_a=self._id_no_none(ganadora_guardada),
            persona_master_id_b=absorbida.id,
            score=resultado.score,
            explicacion=resultado.explicacion,
            campos_utilizados=campos_utilizados,
            creado_en=cuando,
        )
        caso.aprobar(por=f"sistema:auto:{ganadora_guardada.id}", cuando=cuando, criterio="score>=umbral_fusion_automatica")
        caso_guardado = self._caso_revision_repository.guardar(caso)

        evento = generar_evento_persona_fusionada(
            self._id_no_none(ganadora_guardada), self._id_no_none(absorbida), resultado.score, cuando
        )
        self._evento_perfil_repository.guardar(evento)

        logger.info(
            "fusion_automatica_ejecutada",
            persona_master_ganadora_id=ganadora_guardada.id,
            persona_master_absorbida_id=absorbida.id,
            score=resultado.score,
        )
        return DecisionFusionDTO(
            decision=DecisionFusion.FUSION_AUTOMATICA,
            score=resultado.score,
            persona_master_resultante_id=self._id_no_none(ganadora_guardada),
            caso_revision_id=str(caso_guardado.uuid),
            explicacion=resultado.explicacion,
        )

    def _crear_caso_revision(
        self,
        persona_master_nueva: PersonaMaster,
        resultado: IdentityResolutionResultDTO,
        campos_utilizados: tuple[str, ...],
        cuando: datetime,
    ) -> DecisionFusionDTO:
        persona_master_nueva.marcar_en_revision()
        guardada = self._persona_master_repository.guardar(persona_master_nueva)

        caso = CasoRevisionIdentidad(
            persona_master_id_a=resultado.persona_master_id or self._id_no_none(guardada),
            persona_master_id_b=guardada.id if resultado.persona_master_id is not None else None,
            score=resultado.score,
            explicacion=resultado.explicacion,
            campos_utilizados=campos_utilizados,
            creado_en=cuando,
        )
        caso_guardado = self._caso_revision_repository.guardar(caso)

        logger.info(
            "caso_revision_identidad_creado",
            persona_master_id=guardada.id,
            score=resultado.score,
            caso_id=str(caso_guardado.uuid),
        )
        return DecisionFusionDTO(
            decision=DecisionFusion.REVISION_MANUAL,
            score=resultado.score,
            persona_master_resultante_id=self._id_no_none(guardada),
            caso_revision_id=str(caso_guardado.uuid),
            explicacion=resultado.explicacion,
        )

    def revisar_caso(self, caso_id: uuid.UUID, aprobar: bool, revisor: str, cuando: datetime) -> CasoRevisionIdentidad:
        """Resolucion MANUAL de un caso PENDIENTE_REVISION (futuro
        dashboard). Aprobar ejecuta la fusion real; rechazar reactiva la
        PersonaMaster candidata como identidad independiente."""
        caso = self._caso_revision_repository.buscar_por_id(caso_id)
        if caso is None:
            raise PersonaMasterInvalidaError(f"CasoRevisionIdentidad no encontrado: {caso_id}")

        if aprobar:
            caso.aprobar(revisor, cuando)
            if caso.persona_master_id_b is not None:
                self._ejecutar_fusion_manual(caso.persona_master_id_a, caso.persona_master_id_b, caso.score, cuando)
        else:
            caso.rechazar(revisor, cuando)
            if caso.persona_master_id_b is not None:
                candidata = self._persona_master_repository.buscar_por_id(caso.persona_master_id_b)
                if candidata is not None:
                    candidata.marcar_activa()
                    self._persona_master_repository.guardar(candidata)

        return self._caso_revision_repository.guardar(caso)

    def _ejecutar_fusion_manual(
        self, persona_master_id_a: int, persona_master_id_b: int, score: float, cuando: datetime
    ) -> None:
        ganadora = self._persona_master_repository.buscar_por_id(persona_master_id_a)
        perdedora = self._persona_master_repository.buscar_por_id(persona_master_id_b)
        if ganadora is None or perdedora is None:
            raise PersonaMasterInvalidaError("PersonaMaster involucrada en la fusion manual no encontrada")

        perdedora.fusionar_en(self._id_no_none(ganadora))
        self._persona_master_repository.guardar(perdedora)
        ganadora.registrar_nueva_fuente()
        ganadora.marcar_activa()
        self._persona_master_repository.guardar(ganadora)

        evento = generar_evento_persona_fusionada(
            self._id_no_none(ganadora), self._id_no_none(perdedora), score, cuando
        )
        self._evento_perfil_repository.guardar(evento)

    @staticmethod
    def _id_no_none(persona_master: PersonaMaster) -> int:
        if persona_master.id is None:
            raise PersonaMasterInvalidaError("PersonaMaster sin id asignado tras guardar")
        return persona_master.id
