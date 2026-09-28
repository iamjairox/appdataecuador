"""DTO: ResultadoEnriquecimientoAcademicoDTO -- resumen de UNA corrida
del pipeline de Enriquecimiento Academico (Submodulo 7.11) para una
PersonaMaster -- analogo a `ResultadoEnriquecimientoDTO` (Modulo 6)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ResultadoEnriquecimientoAcademicoDTO:
    persona_master_id: int
    consultado: bool
    """`False` cuando la respuesta vino integramente del cache (Submodulo
    7.10) -- no se llamo a SENESCYT."""
    titulos_nuevos: int = 0
    titulos_eliminados: int = 0
    cambios_detectados: int = 0
    alertas_generadas: int = 0
    eventos_generados: int = 0
    duracion_segundos: float = 0.0
    error: str | None = None
    tipos_cambio: list[str] = field(default_factory=list)
