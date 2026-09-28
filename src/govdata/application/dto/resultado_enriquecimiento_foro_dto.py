"""DTO: ResultadoEnriquecimientoForoDTO -- resumen de UNA corrida del
pipeline de consulta al Foro de Abogados (Submodulo 8.12) para una
PersonaMaster -- analogo a `ResultadoEnriquecimientoAcademicoDTO`
(Modulo 7)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ResultadoEnriquecimientoForoDTO:
    persona_master_id: int
    consultado: bool
    """`False` cuando la respuesta vino integramente del cache (Submodulo
    8.8) -- no se llamo al Foro."""
    registros_nuevos: int = 0
    registros_eliminados: int = 0
    cambios_detectados: int = 0
    alertas_generadas: int = 0
    eventos_generados: int = 0
    duracion_segundos: float = 0.0
    error: str | None = None
    tipos_cambio: list[str] = field(default_factory=list)
