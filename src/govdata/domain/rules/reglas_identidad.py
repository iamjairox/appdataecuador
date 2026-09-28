"""Estructuras de datos del Motor de Identidad (Modulo 6) -- puros
contenedores de configuracion (sin IO), mismo patron que
`reglas_configurables.py` (Modulos 4/5) y `reglas_foro.py` (Modulo 8).

Archivo NUEVO e independiente: Modulos 1-5 estan congelados.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError


@dataclass(frozen=True, slots=True)
class PesosScoring:
    """Pesos del Scoring Engine (Submodulo 6.3)."""

    fingerprint: float = 0.30
    correo: float = 0.20
    nombre: float = 0.20
    apellido: float = 0.15
    institucion: float = 0.10
    cargo: float = 0.05
    umbral_minimo_coincidencia: float = 75.0

    def __post_init__(self) -> None:
        total = (
            self.fingerprint + self.correo + self.nombre
            + self.apellido + self.institucion + self.cargo
        )
        if not (0.99 <= total <= 1.01):
            raise ConfiguracionInvalidaError(f"Los pesos deben sumar 1.0 (actual: {total})")


@dataclass(frozen=True, slots=True)
class UmbralesFusion:
    """Umbrales del Motor de Confianza y Fusion (Submodulo 6.21)."""

    umbral_fusion_automatica: float = 98.0
    umbral_revision_manual: float = 85.0


@dataclass(frozen=True, slots=True)
class ReglasCachePorFuente:
    """Vigencia del cache por fuente externa."""

    dias_por_fuente: dict[str, int] = field(default_factory=dict)
    dias_defecto: int = 7

    def dias_vigencia(self, fuente: str) -> int:
        """Retorna los dias de vigencia para una fuente dada."""
        return self.dias_por_fuente.get(fuente, self.dias_defecto)


@dataclass(frozen=True, slots=True)
class ReglaPrioridadPorPalabras:
    """Regla de priorizacion por palabras clave."""

    grupos: tuple[tuple[str, ...], ...]
    prioridad: float


@dataclass(frozen=True, slots=True)
class ReglasPriorizacion:
    """Priorizacion de personas para enriquecimiento (Submodulo 6.11)."""

    prioridad_por_cargo: dict[str, float] = field(default_factory=dict)
    prioridad_defecto: float = 10.0
    umbral_score_minimo: float = 80.0
    reglas_por_palabras: tuple[ReglaPrioridadPorPalabras, ...] = ()


@dataclass(frozen=True, slots=True)
class RuleEngineIdentidad:
    """Punto unico de acceso a toda la configuracion externa del Modulo 6."""

    scoring: PesosScoring
    fusion: UmbralesFusion
    cache_por_fuente: ReglasCachePorFuente
    priorizacion: ReglasPriorizacion
