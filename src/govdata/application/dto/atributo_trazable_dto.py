"""DTO: AtributoTrazableDTO -- forma serializable de `AtributoTrazable`
(Submodulo 6.15, trazabilidad: quien/cuando/fuente/score de cada dato)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.entities.atributo_trazable import AtributoTrazable


@dataclass(frozen=True, slots=True)
class AtributoTrazableDTO:
    campo: str
    valor: str
    fuente: str
    obtenido_en: datetime
    score: float
    registro_fuente_id: int | None = None

    @classmethod
    def desde_entidad(cls, atributo: AtributoTrazable) -> AtributoTrazableDTO:
        return cls(
            campo=atributo.campo,
            valor=atributo.valor,
            fuente=atributo.fuente.value,
            obtenido_en=atributo.obtenido_en,
            score=atributo.score,
            registro_fuente_id=atributo.registro_fuente_id,
        )
