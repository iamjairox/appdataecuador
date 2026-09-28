"""Estructuras de datos del Motor de Identidad -- puramente contenedores
de configuracion (sin IO), mismo patron que `reglas_configurables.py`
(Modulos 4/5, congelado -- por eso este es un archivo NUEVO en vez de una
extension de aquel: Modulo 6 no debe tocar ni un byte de codigo ya
aprobado).

`config/rule_engine_identidad.py` (infraestructura) es el UNICO que sabe
que esto se carga desde YAML; el dominio solo conoce estos tipos.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError

_TOLERANCIA_SUMA_PESOS = 0.01


@dataclass(frozen=True, slots=True)
class PesosScoring:
    """Ponderacion configurable del Scoring Engine (Submodulo 6.3). Debe
    sumar 1.0 (100%) -- se valida al construir, nunca en tiempo de uso."""

    fingerprint: float
    correo: float
    nombre: float
    apellido: float
    institucion: float
    cargo: float
    umbral_minimo_coincidencia: float = 60.0
    """Por debajo de este score compuesto, ni siquiera se considera la
    mejor candidata como una coincidencia posible (SIN_COINCIDENCIA)."""

    def __post_init__(self) -> None:
        total = self.fingerprint + self.correo + self.nombre + self.apellido + self.institucion + self.cargo
        if abs(total - 1.0) > _TOLERANCIA_SUMA_PESOS:
            raise ConfiguracionInvalidaError(
                f"Los pesos de scoring de identidad deben sumar 1.0 (100%), suman {total}"
            )


@dataclass(frozen=True, slots=True)
class UmbralesFusion:
    """Motor de Confianza y Revision Manual (Submodulo 6.21)."""

    umbral_fusion_automatica: float = 98.0
    umbral_revision_manual: float = 85.0

    def __post_init__(self) -> None:
        if not (0.0 <= self.umbral_revision_manual <= self.umbral_fusion_automatica <= 100.0):
            raise ConfiguracionInvalidaError(
                "umbrales de fusion invalidos: se requiere "
                f"0 <= umbral_revision_manual ({self.umbral_revision_manual}) "
                f"<= umbral_fusion_automatica ({self.umbral_fusion_automatica}) <= 100"
            )


@dataclass(frozen=True, slots=True)
class ReglasCachePorFuente:
    """Vigencia del cache, independiente por fuente (Submodulo 6.8)."""

    dias_por_fuente: dict[str, int] = field(default_factory=dict)
    dias_defecto: int = 7

    def dias_vigencia(self, fuente: str) -> int:
        return self.dias_por_fuente.get(fuente, self.dias_defecto)


@dataclass(frozen=True, slots=True)
class ReglaPrioridadPorPalabras:
    """El cargo contiene, como palabra completa y en cualquier orden, al
    menos una alternativa de CADA grupo: `(("PROCURADOR", "PROCURADORA"),
    ("SINDICO", "SINDICA"))` acepta "PROCURADORA SINDICA MUNICIPAL"."""

    grupos: tuple[tuple[str, ...], ...]
    prioridad: float


@dataclass(frozen=True, slots=True)
class ReglasPriorizacion:
    """Motor de Priorizacion (Submodulo 6.11): que Personas enriquecer
    primero, segun el cargo que ocupan."""

    prioridad_por_cargo: dict[str, float] = field(default_factory=dict)
    prioridad_defecto: float = 10.0
    umbral_score_minimo: float = 80.0
    reglas_por_palabras: tuple[ReglaPrioridadPorPalabras, ...] = ()
    """Evaluadas en orden (la primera que acierta gana): los cargos reales
    son frases largas ("DIRECTOR/A DE ASESORIA JURIDICA") que el fuzzy
    match de `prioridad_por_cargo` no alcanza."""


@dataclass(frozen=True, slots=True)
class RuleEngineIdentidad:
    """Punto unico de acceso a toda la configuracion externa del Modulo 6."""

    scoring: PesosScoring
    fusion: UmbralesFusion
    cache_por_fuente: ReglasCachePorFuente
    priorizacion: ReglasPriorizacion
