"""Estructuras de datos del Motor de Consulta al Foro de Abogados --
puros contenedores de configuracion (sin IO), mismo patron que
`reglas_academicas.py` (Modulo 7). Archivo NUEVO e independiente: Modulos
1-7 estan congelados."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CatalogoCamposForo:
    """Etiqueta de campo (tal como aparece en el HTML del Foro, ej. "No.
    Registro:") -> nombre canonico del campo (ej. "registro") -- Submodulo
    8.3. La etiqueta se normaliza (mayuscula, sin tildes/puntuacion) antes
    de comparar, para que "No. Registro" y "NO REGISTRO" resuelvan igual."""

    campo_por_etiqueta: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReglasCacheForo:
    """Vigencia del cache por persona (Submodulo 8.8)."""

    dias_vigencia: int = 7


@dataclass(frozen=True, slots=True)
class ReglasCircuitoForo:
    """Circuit Breaker del adaptador del Foro (Submodulo 8.9)."""

    umbral_fallos: int = 5
    """Fallos consecutivos que abren el circuito."""
    segundos_enfriamiento: float = 60.0
    """Tiempo que el circuito permanece ABIERTO antes de pasar a
    SEMI_ABIERTO (permitir un intento de prueba)."""


@dataclass(frozen=True, slots=True)
class RuleEngineForo:
    """Punto unico de acceso a toda la configuracion externa del Modulo 8."""

    campos: CatalogoCamposForo
    cache: ReglasCacheForo
    circuito: ReglasCircuitoForo
