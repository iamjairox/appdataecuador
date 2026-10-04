"""Estructuras de datos del Motor de Reglas (Modulos 4/5) -- puros
contenedores de configuracion (sin IO), mismo patron que
`reglas_academicas.py` (Modulo 7) y `reglas_foro.py` (Modulo 8).

Archivo NUEVO e independiente: Modulos 1-3 estan congelados.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReglasNormalizacion:
    """Sinonimos de columnas: encabezado canonico -> lista de sinonimos."""

    sinonimos_por_campo: dict[str, list[str]] = field(default_factory=dict)
    nombres_pila: frozenset[str] = frozenset()
    """Nombres de pila comunes (`config/rules/nombres_pila.yaml`, ya
    normalizados) para deducir el orden real de una columna combinada de
    nombre cuando el contenido contradice al encabezado. Vacio = se usa
    solo el encabezado (comportamiento anterior)."""


@dataclass(frozen=True, slots=True)
class ReglasClasificacion:
    """Clasificacion de funcionarios por area (juridica/financiera)."""

    umbral_score_minimo: float = 80.0
    nivel_alta: float = 92.0
    nivel_media: float = 80.0
    cargos_por_area: dict[str, list[str]] = field(default_factory=dict)
    palabras_clave_por_area: dict[str, list[str]] = field(default_factory=dict)
    palabras_clave_dependencia_por_area: dict[str, list[str]] = field(default_factory=dict)
    cargos_habilitantes_dependencia_por_area: dict[str, list[str]] = field(default_factory=dict)
    cargos_excluidos_dependencia_por_area: dict[str, list[str]] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReglasCache:
    """Vigencia del cache por entidad."""

    dias_vigencia: int = 1


@dataclass(frozen=True, slots=True)
class ReglasCriticidad:
    """Criticidad de cambios segun cargo/campo modificado."""

    umbral_score_minimo: float = 80.0
    cargos_criticos: list[str] = field(default_factory=list)
    cargos_altos: list[str] = field(default_factory=list)
    campos_medios: list[str] = field(default_factory=list)
    umbral_cambio_masivo_pct: float = 30.0
    umbral_cambio_masivo_absoluto: int = 15


@dataclass(frozen=True, slots=True)
class RuleEngine:
    """Punto unico de acceso a toda la configuracion externa de Modulos 4/5."""

    normalizacion: ReglasNormalizacion
    clasificacion: ReglasClasificacion
    cache: ReglasCache
    criticidad: ReglasCriticidad
