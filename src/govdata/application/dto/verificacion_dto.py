"""DTO: VerificacionDTO -- forma serializable de `Verificacion`
(Submodulos 5.10/5.15)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.entities.verificacion import Verificacion


@dataclass(frozen=True, slots=True)
class VerificacionDTO:
    entidad_id: int
    hubo_cambio: bool
    motivo: str
    verificado_en: datetime
    documento_id: int | None = None
    hash_verificado: str | None = None

    @classmethod
    def desde_entidad(cls, verificacion: Verificacion) -> VerificacionDTO:
        return cls(
            entidad_id=verificacion.entidad_id,
            hubo_cambio=verificacion.hubo_cambio,
            motivo=verificacion.motivo,
            verificado_en=verificacion.verificado_en,
            documento_id=verificacion.documento_id,
            hash_verificado=verificacion.hash_verificado,
        )
