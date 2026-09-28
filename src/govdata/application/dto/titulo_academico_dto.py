"""DTO: TituloAcademicoDTO -- forma serializable de `TituloAcademico`
(Submodulo 7.6), incluye los metadatos de confiabilidad por fuente
(Submodulo 7.20, mejora 1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from govdata.domain.entities.titulo_academico import TituloAcademico


@dataclass(frozen=True, slots=True)
class TituloAcademicoDTO:
    id: int | None
    persona_master_id: int
    clave_titulo: str
    titulo: str
    nivel: str
    institucion: str
    fecha_registro: date | None
    pais: str | None
    estado: str
    modalidad: str | None
    numero_registro: str | None
    area_conocimiento: str | None
    tipo_titulo: str | None
    fecha_graduacion: date | None
    observaciones: str | None
    numero_version: int
    vigente: bool
    fuente: str
    fecha_consulta: datetime | None
    nivel_confianza: float
    version_fuente: int
    evidencia: str | None

    @classmethod
    def desde_entidad(cls, titulo: TituloAcademico) -> TituloAcademicoDTO:
        return cls(
            id=titulo.id, persona_master_id=titulo.persona_master_id, clave_titulo=titulo.clave_titulo,
            titulo=titulo.titulo, nivel=titulo.nivel, institucion=titulo.institucion,
            fecha_registro=titulo.fecha_registro, pais=titulo.pais, estado=titulo.estado.value,
            modalidad=titulo.modalidad, numero_registro=titulo.numero_registro,
            area_conocimiento=titulo.area_conocimiento, tipo_titulo=titulo.tipo_titulo,
            fecha_graduacion=titulo.fecha_graduacion, observaciones=titulo.observaciones,
            numero_version=titulo.numero_version, vigente=titulo.vigente, fuente=titulo.fuente,
            fecha_consulta=titulo.fecha_consulta, nivel_confianza=titulo.nivel_confianza,
            version_fuente=titulo.version_fuente, evidencia=titulo.evidencia,
        )
