"""DTO: EntidadDescubiertaDTO.

Salida cruda de `PortalScraperPort.listar_entidades()`, antes de mapearla
a la entidad de dominio `Entidad` (que valida invariantes).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EntidadDescubiertaDTO:
    """Una entidad tal como aparece listada en el portal de origen."""

    nombre: str
    url_transparencia: str
    portal_origen: str
    identificador_portal: str | None = None
    tipo_institucion: str | None = None
    activo: bool = True
