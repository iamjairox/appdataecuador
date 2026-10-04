"""DTO: RegistroForoPersistidoDTO -- forma serializable de `RegistroForo`
(Submodulo 8.1), incluye los metadatos de confiabilidad por fuente (mismo
patron que `TituloAcademicoDTO`, Modulo 7)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.entities.registro_foro import RegistroForo


@dataclass(frozen=True, slots=True)
class RegistroForoPersistidoDTO:
    id: int | None
    persona_master_id: int
    clave_registro: str
    nombre_completo: str | None
    registro: str | None
    provincia: str | None
    estado: str
    cedula: str | None
    correo_personal: str | None
    celular_personal: str | None
    numero_version: int
    vigente: bool
    fuente: str
    fecha_consulta: datetime | None
    nivel_confianza: float
    version_fuente: int
    evidencia: str | None

    @classmethod
    def desde_entidad(cls, registro: RegistroForo) -> RegistroForoPersistidoDTO:
        return cls(
            id=registro.id, persona_master_id=registro.persona_master_id, clave_registro=registro.clave_registro,
            nombre_completo=registro.nombre_completo, registro=registro.registro, provincia=registro.provincia,
            estado=registro.estado.value, cedula=registro.cedula, correo_personal=registro.correo_personal,
            celular_personal=registro.celular_personal, numero_version=registro.numero_version,
            vigente=registro.vigente, fuente=registro.fuente, fecha_consulta=registro.fecha_consulta,
            nivel_confianza=registro.nivel_confianza, version_fuente=registro.version_fuente,
            evidencia=registro.evidencia,
        )
