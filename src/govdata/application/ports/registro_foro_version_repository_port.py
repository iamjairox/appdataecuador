"""Puerto: RegistroForoVersionRepositoryPort -- Submodulos 8.6/8.14
(Historial/Versionado)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.registro_foro_version import RegistroForoVersion


class RegistroForoVersionRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, version: RegistroForoVersion) -> RegistroForoVersion:
        """Inserta una version NUEVA. Nunca sobreescribe una version existente."""

    @abstractmethod
    def buscar_vigente(self, persona_master_id: int, clave_registro: str) -> RegistroForoVersion | None: ...

    @abstractmethod
    def listar_historial(self, persona_master_id: int, clave_registro: str) -> list[RegistroForoVersion]:
        """Todas las versiones de UN registro, en orden -- PersonaMaster
        -> Version Foro 1 -> Version Foro 2 -> ..."""

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[RegistroForoVersion]:
        """Todas las versiones, de todos los registros -- insumo del
        Perfil Consolidado (Submodulo 8.10)."""
