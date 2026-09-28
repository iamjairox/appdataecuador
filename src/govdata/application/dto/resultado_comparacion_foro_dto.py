"""DTO: ResultadoComparacionForoDTO -- salida interna del pipeline de
consulta al Foro (agrupa `DiferenciaRegistroForoDTO` por categoria). No es
un contrato oficial -- es el resultado de UNA corrida de comparacion,
consumido por `EnriquecimientoForoService`."""

from __future__ import annotations

from dataclasses import dataclass, field

from govdata.application.dto.diferencia_registro_foro_dto import DiferenciaRegistroForoDTO


@dataclass(frozen=True, slots=True)
class ResultadoComparacionForoDTO:
    persona_master_id: int
    nuevos: list[DiferenciaRegistroForoDTO] = field(default_factory=list)
    eliminados: list[DiferenciaRegistroForoDTO] = field(default_factory=list)
    cambios: list[DiferenciaRegistroForoDTO] = field(default_factory=list)
    sin_cambios: list[DiferenciaRegistroForoDTO] = field(default_factory=list)
