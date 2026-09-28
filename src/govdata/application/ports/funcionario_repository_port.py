"""Puerto: FuncionarioRepositoryPort."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.application.dto.filtros_consulta_dto import FiltrosConsultaDTO
from govdata.domain.entities.funcionario import Funcionario


class FuncionarioRepositoryPort(ABC):
    """Persistencia de vinculos Persona-Entidad-Cargo."""

    @abstractmethod
    def guardar(self, funcionario: Funcionario) -> Funcionario: ...

    @abstractmethod
    def guardar_lote(self, funcionarios: list[Funcionario]) -> list[Funcionario]: ...

    @abstractmethod
    def buscar_vigente(self, persona_id: int, entidad_id: int) -> Funcionario | None:
        """Busca el vinculo vigente (fecha_fin=None) de una persona en una entidad."""

    @abstractmethod
    def listar_por_entidad(self, entidad_id: int, solo_vigentes: bool = True) -> list[Funcionario]: ...

    @abstractmethod
    def listar_por_documento(self, documento_id: int) -> list[Funcionario]:
        """Funcionarios extraidos de un documento especifico -- usado por
        `CacheService` para decidir si ya existe extraccion vigente para
        la VERSION actual de ese documento."""

    @abstractmethod
    def buscar_con_filtros(self, filtros: FiltrosConsultaDTO) -> list[Funcionario]:
        """Consulta funcionarios YA PERSISTIDOS aplicando los filtros dados
        (Submodulo 4.7). Nunca dispara descubrimiento/descarga -- es de
        solo lectura sobre lo que ya existe en base de datos."""
