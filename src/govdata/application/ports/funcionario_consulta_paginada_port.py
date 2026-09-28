"""Puerto: FuncionarioConsultaPaginadaPort -- Modulo 10 (API REST).

NUEVO y propio del Modulo 10: `FuncionarioRepositoryPort` (Modulo 4,
congelado) no expone paginacion a nivel SQL (`listar_por_entidad`/
`buscar_con_filtros` retornan la lista COMPLETA) -- pensado para el uso
interno del pipeline de extraccion/comparacion, donde el universo ya esta
acotado por entidad+documento. El endpoint HTTP `GET /entidades/{id}/funcionarios`
si necesita evitar cargar en memoria entidades con miles de funcionarios
(Submodulo 10.33 "rendimiento": nunca N+1, nunca cargar todo por pedir la
pagina 1).

En vez de modificar el puerto/adaptador de Modulo 4 (prohibido -- Modulos
1-9 quedan congelados), se define este puerto NUEVO, con su propio
adaptador SQLAlchemy de SOLO LECTURA sobre los mismos modelos ORM ya
existentes (`FuncionarioModel`/`PersonaModel`/`PersonaMasterModel`) --
mismo patron ya usado por el propio Modulo 9 para no reabrir Modulo 8."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.application.dto.filtros_funcionario_listado_dto import FiltrosFuncionarioListadoDTO
from govdata.application.dto.funcionario_listado_dto import FuncionarioListadoDTO


class FuncionarioConsultaPaginadaPort(ABC):
    """Lectura paginada, filtrada, de solo informacion YA PERSISTIDA."""

    @abstractmethod
    def buscar_paginado(
        self,
        entidad_id: int,
        filtros: FiltrosFuncionarioListadoDTO,
        page: int,
        page_size: int,
    ) -> tuple[list[FuncionarioListadoDTO], int]:
        """Retorna `(items_de_la_pagina, total_de_registros_que_matchean)`."""
