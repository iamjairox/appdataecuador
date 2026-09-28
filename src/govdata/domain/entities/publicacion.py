"""Entidad de dominio: PublicacionMensual."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from govdata.domain.exceptions.domain_exceptions import GovDataError


class PublicacionInvalidaError(GovDataError):
    """Una PublicacionMensual no cumple sus invariantes."""


@dataclass(slots=True)
class PublicacionMensual:
    """El mes de Transparencia Activa detectado como el mas reciente
    publicado para una Entidad, y la url del item de interes dentro de el.
    """

    entidad_id: int
    mes_publicado: date
    url_item: str
    id: int | None = None
    detectado_en: datetime | None = None

    def __post_init__(self) -> None:
        if not self.url_item or not self.url_item.strip():
            raise PublicacionInvalidaError(
                f"PublicacionMensual (entidad_id={self.entidad_id}) requiere url_item"
            )
        self.url_item = self.url_item.strip()
