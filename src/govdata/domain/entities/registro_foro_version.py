"""Entidad de dominio: RegistroForoVersion -- Submodulos 8.6/8.14
(Historial, Versionado).

    PersonaMaster -> Version Foro 1 -> Version Foro 2 -> ...

"Guardar todas las versiones. Append Only." / "Nunca eliminar versiones."
Cada vez que el Comparador Foro (8.5) detecta un cambio real sobre un
`clave_registro`, la version VIGENTE se cierra (`fecha_fin`) y se abre la
siguiente -- mismo patron exacto que `TituloVersionAcademica` (Modulo 7)
y `VersionFuncionario` (Modulo 5)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from govdata.domain.exceptions.domain_exceptions import RegistroForoVersionInvalidaError
from govdata.domain.value_objects.estado_registro_foro import EstadoRegistroForo


class EstadoVersionForo(str, Enum):
    VIGENTE = "vigente"
    CERRADA = "cerrada"


@dataclass(slots=True)
class RegistroForoVersion:
    """Una version (snapshot en el tiempo) de UN registro (`clave_registro`)."""

    persona_master_id: int
    clave_registro: str
    numero_version: int
    fecha_inicio: date
    """`origen`: la ConsultaForo que produjo esta version (Submodulo 8.14)."""
    consulta_foro_id: int
    id: int | None = None
    nombre_completo: str | None = None
    registro: str | None = None
    provincia: str | None = None
    estado: EstadoRegistroForo = EstadoRegistroForo.DESCONOCIDO
    cedula: str | None = None
    fecha_fin: date | None = None
    estado_version: EstadoVersionForo = EstadoVersionForo.VIGENTE
    creado_en: datetime | None = None

    def __post_init__(self) -> None:
        if self.numero_version < 1:
            raise RegistroForoVersionInvalidaError(f"numero_version invalida: {self.numero_version}")
        if self.fecha_fin is not None and self.fecha_fin < self.fecha_inicio:
            raise RegistroForoVersionInvalidaError(
                f"fecha_fin ({self.fecha_fin}) no puede ser anterior a fecha_inicio ({self.fecha_inicio})"
            )
        if self.estado_version == EstadoVersionForo.VIGENTE and self.fecha_fin is not None:
            raise RegistroForoVersionInvalidaError("Una version VIGENTE no puede tener fecha_fin")
        if self.estado_version == EstadoVersionForo.CERRADA and self.fecha_fin is None:
            raise RegistroForoVersionInvalidaError("Una version CERRADA requiere fecha_fin")

    def cerrar(self, fecha_fin: date) -> None:
        if self.estado_version != EstadoVersionForo.VIGENTE:
            raise RegistroForoVersionInvalidaError(
                f"Solo una version VIGENTE puede cerrarse (estado actual: {self.estado_version.value})"
            )
        if fecha_fin < self.fecha_inicio:
            raise RegistroForoVersionInvalidaError(f"No se puede cerrar antes de fecha_inicio ({self.fecha_inicio})")
        self.fecha_fin = fecha_fin
        self.estado_version = EstadoVersionForo.CERRADA

    @property
    def vigente(self) -> bool:
        return self.estado_version == EstadoVersionForo.VIGENTE
