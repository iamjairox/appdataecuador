"""Servicio: IdentityResolutionService -- Submodulo 6.2 (orquestacion).

Traduce `PersonaMaster` ya persistidas a `SenalesIdentidadDTO` y acota el
universo de candidatas via el repositorio (fingerprint exacto -> fonetico
-> correo, NUNCA un listado completo), antes de delegar la comparacion en
si al motor de dominio puro (`motor_resolucion_identidad.resolver_identidad`).
Este es el unico lugar que conoce tanto el repositorio como el motor de
dominio -- ni el repositorio ni el motor se conocen entre si.
"""

from __future__ import annotations

from govdata.application.dto.identity_resolution_result_dto import IdentityResolutionResultDTO
from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.application.ports.persona_master_repository_port import PersonaMasterRepositoryPort
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.rules.motor_resolucion_identidad import resolver_identidad
from govdata.domain.rules.reglas_identidad import PesosScoring


def senales_desde_persona_master(
    persona_master: PersonaMaster, cargo: str | None = None, institucion: str | None = None
) -> SenalesIdentidadDTO:
    return SenalesIdentidadDTO(
        nombre=persona_master.nombre_completo.nombres,
        apellido=persona_master.nombre_completo.apellidos,
        correo=str(persona_master.correo_principal) if persona_master.correo_principal else None,
        telefono=str(persona_master.telefono_principal) if persona_master.telefono_principal else None,
        institucion=institucion,
        cargo=cargo,
        fingerprint=persona_master.fingerprint_principal,
        fingerprint_fonetico=persona_master.fingerprint_fonetico,
    )


class IdentityResolutionService:
    def __init__(self, persona_master_repository: PersonaMasterRepositoryPort, pesos: PesosScoring) -> None:
        self._persona_master_repository = persona_master_repository
        self._pesos = pesos

    def buscar_candidatas(self, senales: SenalesIdentidadDTO) -> list[tuple[int, SenalesIdentidadDTO]]:
        """Acota candidatas (nunca escanea toda la tabla): fingerprint
        exacto, luego fonetico, luego correo -- deduplicadas por id."""
        vistas: dict[int, PersonaMaster] = {}

        if senales.fingerprint:
            exacto = self._persona_master_repository.buscar_por_fingerprint_principal(senales.fingerprint)
            if exacto is not None and exacto.id is not None:
                vistas[exacto.id] = exacto

        if senales.fingerprint_fonetico:
            for candidata in self._persona_master_repository.buscar_candidatas_por_fingerprint_fonetico(
                senales.fingerprint_fonetico
            ):
                if candidata.id is not None:
                    vistas.setdefault(candidata.id, candidata)

        if senales.correo:
            for candidata in self._persona_master_repository.buscar_candidatas_por_correo(senales.correo):
                if candidata.id is not None:
                    vistas.setdefault(candidata.id, candidata)

        return [(pm_id, senales_desde_persona_master(pm)) for pm_id, pm in vistas.items()]

    def resolver(self, senales: SenalesIdentidadDTO) -> IdentityResolutionResultDTO:
        candidatas = self.buscar_candidatas(senales)
        return resolver_identidad(senales, candidatas, self._pesos)
