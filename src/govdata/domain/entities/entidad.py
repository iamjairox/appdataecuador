"""Entidad de dominio: Entidad (institucion publica)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from govdata.domain.exceptions.domain_exceptions import EntidadInvalidaError


@dataclass(slots=True)
class Entidad:
    """Una institucion publica listada en un portal de transparencia.

    `portal_origen` identifica la fuente (ej. 'dpe', 'senescyt',
    'funcion_judicial') para que el sistema pueda ser multiportal sin
    ambiguedad sobre de donde vino cada registro.
    """

    nombre: str
    url_transparencia: str
    portal_origen: str
    id: int | None = None
    activo: bool = True
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None
    metadata_extra: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.nombre or not self.nombre.strip():
            raise EntidadInvalidaError("Entidad requiere un nombre no vacio")
        if not self.url_transparencia or not self.url_transparencia.strip():
            raise EntidadInvalidaError(
                f"Entidad '{self.nombre}' requiere una url_transparencia no vacia"
            )
        if not self.portal_origen or not self.portal_origen.strip():
            raise EntidadInvalidaError(
                f"Entidad '{self.nombre}' requiere un portal_origen no vacio"
            )
        self.nombre = self.nombre.strip()
        self.url_transparencia = self.url_transparencia.strip()
        self.portal_origen = self.portal_origen.strip().lower()
