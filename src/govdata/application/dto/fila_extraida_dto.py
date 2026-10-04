"""DTO: FilaExtraidaDTO.

Representa una fila cruda tal como sale de un parser (PDF/XLS/XLSX), ANTES
de pasar por clasificacion de area y validacion de Value Objects. Es el
contrato de transporte entre `DocumentParserPort` y los casos de uso de
clasificacion/persistencia -- evita que el dominio dependa de la forma
interna de un DataFrame de pandas.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FilaExtraidaDTO:
    """Una fila del directorio de personal, en texto crudo sin validar."""

    nombres: str
    apellidos: str
    cargo: str
    dependencia: str
    correo: str | None = None
    telefono: str | None = None
    extension_telefonica: str | None = None
    cedula: str | None = None
    nombre_completo_original: str | None = None
    """Texto tal como vino en una columna combinada ("Apellidos y
    Nombres"); `None` si la fuente trae nombres y apellidos separados."""
    orden_nombre: str | None = None
    """`OrdenNombre.value` deducido del encabezado (solo columna combinada)."""
    confianza_segmentacion: str | None = None
    """`ConfianzaSegmentacion.value` de la division nombres/apellidos."""
    ciudad: str | None = None
