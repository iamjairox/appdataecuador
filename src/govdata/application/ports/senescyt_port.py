"""Puerto: SenescytPort -- Submodulo 7.1.

"Nunca implementar logica en el puerto. Solo contrato." Deliberadamente
un contrato NUEVO y mas rico que el generico `SenescytPort` marcador de
Modulo 6 (`application/ports/fuentes_externas_ports.py`, que solo hereda
`.consultar(senales)` de `ExternalSourcePort` sin agregar nada): ese
archivo esta congelado y documentado como "pendiente de implementacion,
proximo modulo" -- este ES ese proximo modulo, y necesita un contrato con
4 formas de busqueda explicitas, no una generica. `SenescytAdapter`
(Submodulo 7.2) implementa AMBOS: este puerto (para las 4 consultas
especificas) y el `ExternalSourcePort` de Modulo 6 (para poder conectarse,
opcionalmente, al pipeline generico ya existente).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.domain.entities.persona_master import PersonaMaster


class SenescytPort(ABC):
    """Contrato de consulta a SENESCYT -- 4 formas de busqueda (Submodulo 7.1)."""

    @abstractmethod
    def consultar_por_cedula(self, cedula: str) -> list[PersonaAcademicaDTO]:
        """Busqueda por cedula -- la mas precisa cuando se conoce."""

    @abstractmethod
    def consultar_por_nombres(self, nombres: str, apellidos: str) -> list[PersonaAcademicaDTO]:
        """Busqueda por nombres/apellidos -- fallback cuando no hay cedula."""

    @abstractmethod
    def consultar_por_identidad(self, senales: SenalesIdentidadDTO) -> list[PersonaAcademicaDTO]:
        """Busqueda usando las senales de identidad ya resueltas (Modulo 6,
        `SenalesIdentidadDTO`) -- decide internamente la mejor estrategia
        (cedula si esta disponible, si no nombres)."""

    @abstractmethod
    def consultar_por_persona_master(self, persona_master: PersonaMaster) -> list[PersonaAcademicaDTO]:
        """Busqueda a partir de una `PersonaMaster` ya resuelta (Modulo 6) --
        la forma de mas alto nivel, la que usa el pipeline de
        Enriquecimiento Academico (Submodulo 7.11/7.12)."""
