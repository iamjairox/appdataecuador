"""Puerto: IdentityResolutionPort.

Este es el componente senalado como critico: el Motor de Resolucion de
Identidad. Cuando el sistema se vuelva multiportal (Transparencia +
SENESCYT + Funcion Judicial + ...), los nombres de una misma persona
llegaran escritos de forma distinta entre fuentes:

    Fuente 1: "JUAN CARLOS PEREZ"
    Fuente 2: "JUAN C. PEREZ"
    Fuente 3: "PEREZ JUAN CARLOS"

Este puerto define el contrato para decidir si dos registros representan
a la misma Persona. La implementacion (RapidFuzz + reglas de normalizacion
+ umbral de confianza) es un modulo posterior; aqui solo se fija el
contrato para que el resto del sistema (casos de uso de persistencia de
Persona) ya pueda depender de el sin bloquearse.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from govdata.domain.entities.persona import Persona
from govdata.domain.value_objects.nombre_completo import NombreCompleto


class NivelConfianza(str, Enum):
    """Resultado de comparar dos identidades candidatas."""

    COINCIDENCIA_ALTA = "coincidencia_alta"      # auto-merge seguro
    COINCIDENCIA_PROBABLE = "coincidencia_probable"  # requiere revision humana
    SIN_COINCIDENCIA = "sin_coincidencia"


@dataclass(frozen=True, slots=True)
class ResultadoResolucion:
    """Veredicto del motor de identidad sobre un par (candidata, nueva)."""

    persona_candidata: Persona
    score: float  # 0-100, score de similitud (ej. RapidFuzz token_sort_ratio)
    nivel_confianza: NivelConfianza


class IdentityResolutionPort(ABC):
    """Decide si un nombre nuevo corresponde a una Persona ya existente."""

    @abstractmethod
    def resolver(
        self, nombre: NombreCompleto, candidatas: list[Persona]
    ) -> ResultadoResolucion | None:
        """Compara `nombre` contra `candidatas` y retorna el mejor veredicto,
        o None si ninguna candidata supera el umbral minimo de similitud.
        """
