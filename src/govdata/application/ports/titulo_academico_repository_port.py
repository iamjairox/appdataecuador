"""Puerto: TituloAcademicoRepositoryPort -- Submodulo 7.6 (puntero vigente)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.titulo_academico import TituloAcademico


class TituloAcademicoRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, titulo: TituloAcademico) -> TituloAcademico: ...

    @abstractmethod
    def buscar_vigente_por_clave(self, persona_master_id: int, clave_titulo: str) -> TituloAcademico | None: ...

    @abstractmethod
    def listar_vigentes_por_persona_master(self, persona_master_id: int) -> list[TituloAcademico]:
        """Todos los titulos vigentes (Submodulo 7.7, "anteriores" contra
        los que se compara la proxima consulta)."""
