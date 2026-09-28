"""Caso de uso: EnriquecerPersonaUseCase -- Submodulo 6.7.

Traduce una `PersonaMaster` ya resuelta (ver
`ResolverOCrearPersonaMasterUseCase`) a las senales que
`EnriquecimientoService` necesita, y delega en el todo el pipeline. Este
caso de uso es la fachada que un futuro job masivo (o el modulo SENESCYT)
invocara -- nunca construye `SenalesIdentidadDTO` en mas de un lugar.
"""

from __future__ import annotations

from govdata.application.dto.resultado_enriquecimiento_dto import ResultadoEnriquecimientoDTO
from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.application.ports.fuentes_externas_ports import ExternalSourcePort
from govdata.application.services.enriquecimiento_service import EnriquecimientoService
from govdata.domain.entities.persona_master import PersonaMaster


class EnriquecerPersonaUseCase:
    def __init__(self, enriquecimiento_service: EnriquecimientoService) -> None:
        self._enriquecimiento_service = enriquecimiento_service

    def ejecutar(
        self,
        persona_master: PersonaMaster,
        fuentes: list[ExternalSourcePort],
        cargo: str | None = None,
        institucion: str | None = None,
    ) -> ResultadoEnriquecimientoDTO:
        senales = SenalesIdentidadDTO(
            nombre=persona_master.nombre_completo.nombres,
            apellido=persona_master.nombre_completo.apellidos,
            correo=str(persona_master.correo_principal) if persona_master.correo_principal else None,
            telefono=str(persona_master.telefono_principal) if persona_master.telefono_principal else None,
            institucion=institucion,
            cargo=cargo,
            fingerprint=persona_master.fingerprint_principal,
            fingerprint_fonetico=persona_master.fingerprint_fonetico,
        )
        return self._enriquecimiento_service.enriquecer(persona_master, fuentes, senales)
