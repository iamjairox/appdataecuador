"""DTO: RegistroForoVersionDTO -- forma serializable de
`RegistroForoVersion` (Submodulos 8.6/8.14)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from govdata.domain.entities.registro_foro_version import RegistroForoVersion


@dataclass(frozen=True, slots=True)
class RegistroForoVersionDTO:
    id: int | None
    persona_master_id: int
    clave_registro: str
    numero_version: int
    nombre_completo: str | None
    registro: str | None
    provincia: str | None
    estado: str
    fecha_inicio: date
    fecha_fin: date | None
    estado_version: str
    consulta_foro_id: int
    creado_en: datetime | None

    @classmethod
    def desde_entidad(cls, version: RegistroForoVersion) -> RegistroForoVersionDTO:
        return cls(
            id=version.id, persona_master_id=version.persona_master_id, clave_registro=version.clave_registro,
            numero_version=version.numero_version, nombre_completo=version.nombre_completo,
            registro=version.registro, provincia=version.provincia, estado=version.estado.value,
            fecha_inicio=version.fecha_inicio, fecha_fin=version.fecha_fin,
            estado_version=version.estado_version.value, consulta_foro_id=version.consulta_foro_id,
            creado_en=version.creado_en,
        )
