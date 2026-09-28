"""Servicio: TimelinePersonaService -- Submodulo 6.5 (Timeline).

    2019 Municipio Quito -> 2021 Ministerio Salud -> 2023 Procuraduria
    -> 2026 Director Juridico

Combina DOS fuentes de historial sin reimplementar ninguna:
el historial institucional YA EXISTENTE (`HistorialService.historial_de_persona`,
Modulo 5, REUTILIZADO) y las versiones de fuentes externas de este Modulo
(`RegistroFuenteRepositoryPort`) en una unica linea de tiempo ordenada
cronologicamente. "Nunca perder historial": ambas fuentes se conservan
integras, cada punto declara su origen.
"""

from __future__ import annotations

from datetime import date

from govdata.application.dto.timeline_persona_dto import (
    PuntoTimelinePersonaDTO,
    TimelinePersonaDTO,
)
from govdata.application.ports.registro_fuente_repository_port import RegistroFuenteRepositoryPort
from govdata.application.services.historial_service import HistorialService
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError


class TimelinePersonaService:
    def __init__(
        self, historial_service: HistorialService, registro_fuente_repository: RegistroFuenteRepositoryPort
    ) -> None:
        self._historial_service = historial_service
        self._registro_fuente_repository = registro_fuente_repository

    def construir(self, persona_master: PersonaMaster) -> TimelinePersonaDTO:
        if persona_master.id is None:
            raise PersonaMasterInvalidaError("No se puede construir un timeline sin PersonaMaster.id")

        puntos: list[PuntoTimelinePersonaDTO] = []
        for version in self._historial_service.historial_de_persona(persona_master.persona_id):
            puntos.append(
                PuntoTimelinePersonaDTO(
                    fecha_inicio=version.fecha_inicio,
                    fecha_fin=version.fecha_fin,
                    origen="institucional",
                    descripcion=f"{version.cargo} - {version.dependencia}",
                    referencia_id=version.id,
                )
            )

        for registro in self._registro_fuente_repository.listar_por_persona_master(persona_master.id):
            puntos.append(
                PuntoTimelinePersonaDTO(
                    fecha_inicio=registro.consultado_en.date() if registro.consultado_en else None,
                    fecha_fin=None,
                    origen=registro.fuente.value,
                    descripcion=f"{registro.fuente.value} v{registro.version}",
                    referencia_id=registro.id,
                )
            )

        puntos_ordenados = sorted(puntos, key=lambda p: p.fecha_inicio or date.min)
        return TimelinePersonaDTO(persona_master_id=persona_master.id, puntos=puntos_ordenados)
