"""DTO: FiltrosFuncionarioListadoDTO -- Modulo 10 (API REST), endpoint
`GET /entidades/{id}/funcionarios`.

Deliberadamente SEPARADO de `FiltrosConsultaDTO` (Submodulo 4.7, Modulo 4
congelado): ese DTO filtra sobre `FuncionarioRepositoryPort.buscar_con_filtros`
(sin paginacion, pensado para consultas ya acotadas por entidad+area desde
`ConsultaService`); este es el contrato del Modulo 10 para el nuevo puerto
de solo lectura PAGINADO (`FuncionarioConsultaPaginadaPort`) -- agregar un
filtro nuevo aqui es aditivo, nunca reabre Modulo 4.

`provincia`/`estado_foro` se aceptan en el request (mismo campo que pide
la especificacion) pero, igual que `FiltrosConsultaDTO.provincia/ciudad`,
HOY no tienen dato persistido en `funcionarios`/`personas` (esa
informacion vive en el Foro de Abogados, no en Transparencia) -- se
documentan como filtro sin efecto, nunca se inventa el dato."""

from __future__ import annotations

from dataclasses import dataclass

from govdata.domain.value_objects.area_relevante import AreaRelevante


@dataclass(frozen=True, slots=True)
class FiltrosFuncionarioListadoDTO:
    nombre: str | None = None
    apellido: str | None = None
    cedula: str | None = None
    cargo: str | None = None
    dependencia: str | None = None
    area: AreaRelevante | None = None
    correo: str | None = None
    telefono: str | None = None
    solo_vigentes: bool = True
