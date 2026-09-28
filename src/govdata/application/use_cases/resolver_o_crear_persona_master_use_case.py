"""Caso de uso: ResolverOCrearPersonaMasterUseCase -- el UNICO punto de
entrada para dar de alta una `PersonaMaster` (Submodulos 6.1 + 6.2 + 6.21).

"Nunca existiran personas duplicadas: debe existir un unico registro
maestro." Esta garantia depende enteramente de que NINGUN otro lugar del
codigo cree una `PersonaMaster` directamente -- todo alta pasa por aqui:

    1. ¿La `Persona` de origen (Modulo 1-5) ya tiene una PersonaMaster?
       -> se retorna esa (idempotente, nunca duplica).
    2. Si no, se resuelve identidad contra las PersonaMaster existentes
       (Submodulo 6.2) y se decide que hacer con el score (Submodulo 6.21):
       fusion automatica, caso de revision manual, o identidad nueva.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.application.ports.persona_master_repository_port import PersonaMasterRepositoryPort
from govdata.application.services.fusion_service import FusionService
from govdata.application.services.identity_resolution_service import IdentityResolutionService
from govdata.config.logging_config import get_logger
from govdata.domain.entities.persona import Persona
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError
from govdata.domain.rules.generador_fingerprint_fonetico import generar_fingerprint_fonetico

logger = get_logger(__name__)


class ResolverOCrearPersonaMasterUseCase:
    def __init__(
        self,
        persona_master_repository: PersonaMasterRepositoryPort,
        identity_resolution_service: IdentityResolutionService,
        fusion_service: FusionService,
        ahora_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._persona_master_repository = persona_master_repository
        self._identity_resolution_service = identity_resolution_service
        self._fusion_service = fusion_service
        self._ahora_provider = ahora_provider

    def ejecutar(
        self,
        persona: Persona,
        cargo: str | None = None,
        institucion: str | None = None,
        decidido_por: str = "sistema",
    ) -> PersonaMaster:
        if persona.id is None:
            raise PersonaMasterInvalidaError("Persona debe estar persistida (id asignado) antes de resolver su identidad maestra")

        existente = self._persona_master_repository.buscar_por_persona_id(persona.id)
        if existente is not None:
            return existente

        cuando = self._ahora_provider()
        fingerprint_fonetico = generar_fingerprint_fonetico(
            persona.nombre_completo.nombres, persona.nombre_completo.apellidos
        )

        senales = SenalesIdentidadDTO(
            nombre=persona.nombre_completo.nombres,
            apellido=persona.nombre_completo.apellidos,
            correo=str(persona.correo) if persona.correo else None,
            telefono=str(persona.telefono) if persona.telefono else None,
            institucion=institucion,
            cargo=cargo,
            fingerprint=persona.fingerprint,
            fingerprint_fonetico=fingerprint_fonetico,
        )

        candidata_nueva = PersonaMaster(
            persona_id=persona.id,
            nombre_completo=persona.nombre_completo,
            fingerprint_principal=persona.fingerprint,
            fingerprint_fonetico=fingerprint_fonetico,
            correo_principal=persona.correo,
            telefono_principal=persona.telefono,
            creado_en=cuando,
            actualizado_en=cuando,
        )

        resultado = self._identity_resolution_service.resolver(senales)
        decision = self._fusion_service.evaluar_y_decidir(candidata_nueva, resultado, decidido_por)

        resultante = self._persona_master_repository.buscar_por_id(decision.persona_master_resultante_id)
        if resultante is None:
            raise PersonaMasterInvalidaError(
                f"PersonaMaster resultante no encontrada tras la decision: {decision.persona_master_resultante_id}"
            )
        logger.info(
            "persona_master_resuelta",
            persona_id=persona.id,
            persona_master_id=resultante.id,
            decision=decision.decision.value,
            score=decision.score,
        )
        return resultante
