"""Puerto: ForoAbogadosPort -- Submodulo 8.1.

"Crear un puerto completamente nuevo. Nunca reutilizar SenescytPort.
Nunca reutilizar HttpFetcherPort. Debe existir un puerto exclusivo."
Contrato PURO -- ninguna logica de scraping/parsing vive aqui (Submodulo
8.2, "nunca implementar logica en el puerto")."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.domain.entities.persona import Persona
from govdata.domain.entities.persona_master import PersonaMaster


class ForoAbogadosPort(ABC):
    """Contrato de consulta al Foro de Abogados -- 3 formas de busqueda
    (Submodulo 8.1)."""

    @abstractmethod
    def buscar_por_cedula(self, cedula: str) -> list[RegistroForoDTO]:
        """Busqueda directa por cedula -- la forma primaria del Foro (un
        colegio profesional identifica matriculas por documento de
        identidad, no por nombre)."""

    @abstractmethod
    def buscar_por_persona(self, persona: Persona) -> list[RegistroForoDTO]:
        """Busqueda a partir de una `Persona` (Modulo 1-5) ya persistida
        -- usa `persona.cedula` cuando esta disponible (la cedula "ya
        conocida" por el sistema en este punto del flujo, ver Submodulo
        8.11: Transparencia -> ... -> SENESCYT -> Obtener Cedula -> Foro
        de Abogados)."""

    @abstractmethod
    def buscar_por_persona_master(self, persona_master: PersonaMaster) -> list[RegistroForoDTO]:
        """Busqueda a partir de una `PersonaMaster` ya resuelta (Modulo 6)
        -- la forma de mas alto nivel, la que usa el pipeline de consulta
        al Foro (Submodulo 8.12/8.13)."""
