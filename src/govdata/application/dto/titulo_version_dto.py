"""DTO: TituloVersionDTO -- forma serializable de `TituloVersionAcademica`
(Submodulos 7.6/7.14)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from govdata.domain.entities.titulo_version_academica import TituloVersionAcademica


@dataclass(frozen=True, slots=True)
class TituloVersionDTO:
    id: int | None
    persona_master_id: int
    clave_titulo: str
    numero_version: int
    titulo: str
    nivel: str
    institucion: str
    fecha_inicio: date
    fecha_fin: date | None
    estado_version: str
    estado: str
    consulta_senescyt_id: int
    creado_en: datetime | None

    @classmethod
    def desde_entidad(cls, version: TituloVersionAcademica) -> TituloVersionDTO:
        return cls(
            id=version.id, persona_master_id=version.persona_master_id, clave_titulo=version.clave_titulo,
            numero_version=version.numero_version, titulo=version.titulo, nivel=version.nivel,
            institucion=version.institucion, fecha_inicio=version.fecha_inicio, fecha_fin=version.fecha_fin,
            estado_version=version.estado_version.value, estado=version.estado.value,
            consulta_senescyt_id=version.consulta_senescyt_id, creado_en=version.creado_en,
        )
