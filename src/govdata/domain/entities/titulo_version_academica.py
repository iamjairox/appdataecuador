"""Entidad de dominio: TituloVersionAcademica -- Submodulos 7.6/7.14
(Historial Academico, Versionado).

    PersonaMaster -> Version Academica 1 -> Version Academica 2 -> ...

"Nunca eliminar versiones. Siempre conservar que cambio, cuando, quien,
origen, fecha." Cada vez que el Comparador Academico (7.7) detecta un
cambio real sobre un `clave_titulo`, la version VIGENTE se cierra
(`fecha_fin`) y se abre la siguiente -- mismo patron exacto que
`VersionFuncionario` (Modulo 5).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from govdata.domain.exceptions.domain_exceptions import TituloVersionAcademicaInvalidaError
from govdata.domain.value_objects.estado_registro_academico import EstadoRegistroAcademico


class EstadoVersionAcademica(str, Enum):
    VIGENTE = "vigente"
    CERRADA = "cerrada"


@dataclass(slots=True)
class TituloVersionAcademica:
    """Una version (snapshot en el tiempo) de UN titulo (`clave_titulo`)."""

    persona_master_id: int
    clave_titulo: str
    numero_version: int
    titulo: str
    nivel: str
    institucion: str
    fecha_inicio: date
    """`origen`: la ConsultaSenescyt que produjo esta version (Submodulo 7.14)."""
    consulta_senescyt_id: int
    id: int | None = None
    fecha_registro: date | None = None
    pais: str | None = None
    estado: EstadoRegistroAcademico = EstadoRegistroAcademico.DESCONOCIDO
    modalidad: str | None = None
    numero_registro: str | None = None
    area_conocimiento: str | None = None
    tipo_titulo: str | None = None
    fecha_graduacion: date | None = None
    observaciones: str | None = None
    fecha_fin: date | None = None
    estado_version: EstadoVersionAcademica = EstadoVersionAcademica.VIGENTE
    creado_en: datetime | None = None

    def __post_init__(self) -> None:
        if self.numero_version < 1:
            raise TituloVersionAcademicaInvalidaError(f"numero_version invalida: {self.numero_version}")
        if self.fecha_fin is not None and self.fecha_fin < self.fecha_inicio:
            raise TituloVersionAcademicaInvalidaError(
                f"fecha_fin ({self.fecha_fin}) no puede ser anterior a fecha_inicio ({self.fecha_inicio})"
            )
        if self.estado_version == EstadoVersionAcademica.VIGENTE and self.fecha_fin is not None:
            raise TituloVersionAcademicaInvalidaError("Una version VIGENTE no puede tener fecha_fin")
        if self.estado_version == EstadoVersionAcademica.CERRADA and self.fecha_fin is None:
            raise TituloVersionAcademicaInvalidaError("Una version CERRADA requiere fecha_fin")

    def cerrar(self, fecha_fin: date) -> None:
        if self.estado_version != EstadoVersionAcademica.VIGENTE:
            raise TituloVersionAcademicaInvalidaError(
                f"Solo una version VIGENTE puede cerrarse (estado actual: {self.estado_version.value})"
            )
        if fecha_fin < self.fecha_inicio:
            raise TituloVersionAcademicaInvalidaError(f"No se puede cerrar antes de fecha_inicio ({self.fecha_inicio})")
        self.fecha_fin = fecha_fin
        self.estado_version = EstadoVersionAcademica.CERRADA

    @property
    def vigente(self) -> bool:
        return self.estado_version == EstadoVersionAcademica.VIGENTE
