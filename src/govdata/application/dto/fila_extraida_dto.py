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
    cedula: str | None = None
