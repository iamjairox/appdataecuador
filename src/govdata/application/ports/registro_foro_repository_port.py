"""Puerto: RegistroForoRepositoryPort -- Submodulo 8.1 (puntero vigente)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.registro_foro import RegistroForo


class RegistroForoRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, registro: RegistroForo) -> RegistroForo: ...

    @abstractmethod
    def buscar_vigente_por_clave(self, persona_master_id: int, clave_registro: str) -> RegistroForo | None: ...

    @abstractmethod
    def listar_vigentes_por_persona_master(self, persona_master_id: int) -> list[RegistroForo]:
        """Todos los registros vigentes (Submodulo 8.5, "anteriores"
        contra los que se compara la proxima consulta)."""
