"""Estructuras de datos del Motor de Enriquecimiento Academico -- puros
contenedores de configuracion (sin IO), mismo patron que
`reglas_configurables.py` (Modulos 4/5) y `reglas_identidad.py` (Modulo
6). Archivo NUEVO e independiente: Modulos 4/5/6 estan congelados.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CatalogoNormalizacion:
    """Sinonimo -> forma canonica, para UN catalogo (titulos, universidades
    o niveles). Las claves del YAML se normalizan (mayuscula, sin tildes)
    antes de comparar, para que "Ing." y "ING." resuelvan igual."""

    canonico_por_sinonimo: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReglasCacheSenescyt:
    """Vigencia del cache por persona (Submodulo 7.10)."""

    dias_vigencia: int = 30


@dataclass(frozen=True, slots=True)
class RuleEngineAcademico:
    """Punto unico de acceso a toda la configuracion externa del Modulo 7."""

    titulos: CatalogoNormalizacion
    universidades: CatalogoNormalizacion
    niveles: CatalogoNormalizacion
    cache: ReglasCacheSenescyt
