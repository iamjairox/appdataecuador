"""Puerto: PersonaRepositoryPort."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.persona import Persona
from govdata.domain.value_objects.nombre_completo import NombreCompleto


class PersonaRepositoryPort(ABC):
    """Persistencia de Personas (identidad unica entre todas las fuentes)."""

    @abstractmethod
    def guardar(self, persona: Persona) -> Persona:
        """Inserta o actualiza una Persona. Retorna la instancia con `id` asignado."""

    @abstractmethod
    def buscar_por_id(self, persona_id: int) -> Persona | None: ...

    @abstractmethod
    def buscar_por_cedula(self, cedula: str) -> Persona | None: ...

    @abstractmethod
    def buscar_candidatas_por_nombre(self, nombre: NombreCompleto) -> list[Persona]:
        """Retorna candidatas para matching cuando no hay cedula disponible.

        No hace matching difuso (eso es responsabilidad de
        `IdentityResolutionPort`); simplemente acota el universo de
        comparacion, por ejemplo via busqueda por trigramas o similar en
        infraestructura.
        """

    @abstractmethod
    def buscar_por_fingerprint_hash(self, fingerprint_hash: str) -> Persona | None:
        """Deduplicacion EXACTA por huella (Submodulo 4.4): dentro de una
        misma corrida de extraccion, si dos filas producen el mismo
        fingerprint, se asume la misma Persona. Esto NO es la comparacion
        difusa completa de Identity Resolution (etapa futura, cuando
        existan multiples fuentes) -- es la base minima para no duplicar
        Personas al extraer un unico documento.
        """
