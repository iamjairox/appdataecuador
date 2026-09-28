"""DTO: ResultadoEnriquecimientoDTO -- resumen de UNA corrida del pipeline
de Enriquecimiento (Submodulo 6.7) para una PersonaMaster."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ResultadoEnriquecimientoDTO:
    persona_master_id: int
    fuentes_consultadas: list[str] = field(default_factory=list)
    fuentes_omitidas_por_cache: list[str] = field(default_factory=list)
    fuentes_con_error: list[str] = field(default_factory=list)
    eventos_generados: int = 0
    alertas_generadas: int = 0
    duracion_segundos: float = 0.0
