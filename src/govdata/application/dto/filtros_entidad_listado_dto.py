"""DTO: FiltrosEntidadListadoDTO -- Modulo 10 (API REST), `GET /entidades`.

`provincia`/`ciudad` se aceptan (mismos nombres pedidos por la
especificacion) pero HOY no filtran nada real -- ver `EntidadListadoDTO`
para la justificacion completa (Modulo 2 no captura esa informacion)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FiltrosEntidadListadoDTO:
    nombre: str | None = None
    provincia: str | None = None
    ciudad: str | None = None
    tipo_institucion: str | None = None
    portal_origen: str | None = None
