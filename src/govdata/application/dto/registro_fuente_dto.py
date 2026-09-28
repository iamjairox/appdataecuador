"""DTO: RegistroFuenteDTO -- forma serializable de `RegistroFuente`
(Submodulo 6.9)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from govdata.domain.entities.registro_fuente import RegistroFuente


@dataclass(frozen=True, slots=True)
class RegistroFuenteDTO:
    id: int | None
    persona_master_id: int
    fuente: str
    version: int
    datos: dict[str, Any]
    consultado_en: datetime | None
    vigente: bool
    hash_contenido: str | None

    @classmethod
    def desde_entidad(cls, registro: RegistroFuente) -> RegistroFuenteDTO:
        return cls(
            id=registro.id,
            persona_master_id=registro.persona_master_id,
            fuente=registro.fuente.value,
            version=registro.version,
            datos=registro.datos,
            consultado_en=registro.consultado_en,
            vigente=registro.vigente,
            hash_contenido=registro.hash_contenido,
        )
