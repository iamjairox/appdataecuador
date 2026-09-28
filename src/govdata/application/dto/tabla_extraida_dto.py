"""DTO: TablaExtraidaDTO.

Salida CRUDA de un parser (Submodulo 4.1), antes de cualquier
interpretacion semantica. Cada fila es un `dict[str, str]` de
`encabezado_original -> valor_celda`, tal como aparece en el documento --
el parser NO sabe (ni le importa) que columna es "nombre" o "cargo": eso
es responsabilidad exclusiva del Normalizador Universal (Submodulo 4.2).

Deliberadamente NO es un DataFrame ni ningun objeto especifico de
`pandas`/`openpyxl`/`camelot`: es una lista de diccionarios de `str`,
100% serializable y sin dependencias de terceros fuera de este archivo.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TablaExtraidaDTO:
    """Tabla cruda: encabezados originales + filas como dict de texto."""

    encabezados: tuple[str, ...]
    filas: list[dict[str, str]] = field(default_factory=list)

    @property
    def cantidad_filas(self) -> int:
        return len(self.filas)
