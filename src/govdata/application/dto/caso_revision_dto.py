"""DTO: CasoRevisionDTO -- forma serializable de `CasoRevisionIdentidad`
(Submodulo 6.21)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.entities.caso_revision_identidad import CasoRevisionIdentidad


@dataclass(frozen=True, slots=True)
class CasoRevisionDTO:
    id: str
    persona_master_id_a: int
    score: float
    explicacion: str
    campos_utilizados: tuple[str, ...]
    estado: str
    creado_en: datetime
    persona_master_id_b: int | None = None
    registro_fuente_id: int | None = None
    resuelto_en: datetime | None = None
    resuelto_por: str | None = None
    criterio_resolucion: str | None = None

    @classmethod
    def desde_entidad(cls, caso: CasoRevisionIdentidad) -> CasoRevisionDTO:
        return cls(
            id=str(caso.uuid),
            persona_master_id_a=caso.persona_master_id_a,
            score=caso.score,
            explicacion=caso.explicacion,
            campos_utilizados=caso.campos_utilizados,
            estado=caso.estado.value,
            creado_en=caso.creado_en,
            persona_master_id_b=caso.persona_master_id_b,
            registro_fuente_id=caso.registro_fuente_id,
            resuelto_en=caso.resuelto_en,
            resuelto_por=caso.resuelto_por,
            criterio_resolucion=caso.criterio_resolucion,
        )
