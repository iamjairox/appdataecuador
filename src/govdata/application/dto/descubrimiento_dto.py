"""DTOs crudos del flujo de descubrimiento (Modulo 2).

Transportan exactamente lo que el adaptador de scraping observa, sin
ninguna decision de negocio todavia (esa vive en `domain.rules`).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ArchivoDTO:
    """Un archivo adjunto a un numeral publicado (ej. 'Conjunto de datos')."""

    descripcion: str
    nombre: str
    url_descarga: str


@dataclass(frozen=True, slots=True)
class NumeralPublicadoDTO:
    """Un numeral (item regulatorio) publicado en un mes de Transparencia Activa."""

    descripcion: str
    archivos: list[ArchivoDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ResultadoMatchNumeralDTO:
    """Veredicto de la regla de matching difuso sobre un conjunto de numerales."""

    numeral: NumeralPublicadoDTO
    score: float


@dataclass(frozen=True, slots=True)
class ResultadoMatchArchivoDTO:
    """Veredicto de la regla de seleccion del archivo de datos dentro de un numeral."""

    archivo: ArchivoDTO
    score: float
