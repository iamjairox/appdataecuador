"""DTO: ResultadoComparacionAcademicaDTO -- salida interna del pipeline
de Enriquecimiento Academico (agrupa `DiferenciaTituloDTO` por
categoria). No es el contrato oficial (ver `PerfilAcademicoDTO`,
Submodulo 7.16) -- es el resultado de UNA corrida de comparacion,
consumido por `PerfilAcademicoService` para construirlo."""

from __future__ import annotations

from dataclasses import dataclass, field

from govdata.application.dto.diferencia_titulo_dto import DiferenciaTituloDTO


@dataclass(frozen=True, slots=True)
class ResultadoComparacionAcademicaDTO:
    persona_master_id: int
    nuevos: list[DiferenciaTituloDTO] = field(default_factory=list)
    eliminados: list[DiferenciaTituloDTO] = field(default_factory=list)
    cambios: list[DiferenciaTituloDTO] = field(default_factory=list)
    sin_cambios: list[DiferenciaTituloDTO] = field(default_factory=list)
