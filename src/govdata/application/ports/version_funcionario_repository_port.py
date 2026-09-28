"""Puerto: VersionFuncionarioRepositoryPort -- Submodulos 5.2/5.3/5.4."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from govdata.domain.entities.version_funcionario import VersionFuncionario


class VersionFuncionarioRepositoryPort(ABC):
    """Persistencia del historial completo (append-only) de versiones de
    cada vinculo Persona-Entidad-Cargo."""

    @abstractmethod
    def guardar(self, version: VersionFuncionario) -> VersionFuncionario: ...

    @abstractmethod
    def buscar_vigente(self, persona_id: int, entidad_id: int) -> VersionFuncionario | None:
        """La version VIGENTE actual de una persona en una entidad, si existe."""

    @abstractmethod
    def listar_por_persona(self, persona_id: int) -> list[VersionFuncionario]:
        """Todo el historial de una persona, mas antigua primero -- base
        para reconstruir su trayectoria de cargos/dependencias en el tiempo."""

    @abstractmethod
    def listar_por_entidad_y_cargo(self, entidad_id: int, cargo: str) -> list[VersionFuncionario]:
        """Todas las versiones (de cualquier persona) que ocuparon `cargo`
        en `entidad_id` -- responde '¿Cuantos Directores Juridicos tuvo
        esta entidad?' y '¿Quien fue reemplazado?' (Submodulo 5.3)."""

    @abstractmethod
    def buscar_vigente_por_entidad_y_cargo(self, entidad_id: int, cargo: str) -> VersionFuncionario | None:
        """La version VIGENTE que ocupa `cargo` en `entidad_id` HOY --
        responde '¿Quien es el Director Juridico actual?'."""

    @abstractmethod
    def buscar_vigente_en_fecha(self, entidad_id: int, cargo: str, en_fecha: date) -> VersionFuncionario | None:
        """La version que ocupaba `cargo` en `entidad_id` en `en_fecha`
        (fecha_inicio <= en_fecha <= fecha_fin O fecha_fin es None) --
        responde '¿Quien era Director Juridico en junio?'."""

    @abstractmethod
    def listar_por_entidad(self, entidad_id: int) -> list[VersionFuncionario]:
        """Todo el historial de una entidad -- base del Timeline (5.13) y
        del historial de dependencia (5.4)."""
