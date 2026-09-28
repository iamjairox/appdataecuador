"""Puerto: TituloVersionRepositoryPort -- Submodulos 7.6/7.14 (Historial/Versionado)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.titulo_version_academica import TituloVersionAcademica


class TituloVersionRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, version: TituloVersionAcademica) -> TituloVersionAcademica:
        """Inserta una version NUEVA. Nunca sobreescribe una version existente."""

    @abstractmethod
    def buscar_vigente(self, persona_master_id: int, clave_titulo: str) -> TituloVersionAcademica | None: ...

    @abstractmethod
    def listar_historial(self, persona_master_id: int, clave_titulo: str) -> list[TituloVersionAcademica]:
        """Todas las versiones de UN titulo, en orden -- PersonaMaster ->
        Version Academica 1 -> Version Academica 2 -> ..."""

    @abstractmethod
    def listar_por_persona_master(self, persona_master_id: int) -> list[TituloVersionAcademica]:
        """Todas las versiones, de todos los titulos -- insumo del
        contrato oficial (`titulos`, Submodulo 7.16)."""
