"""Entidad de dominio: VersionFuncionario -- Submodulos 5.2/5.3/5.4.

Nunca se sobrescribe informacion: cada vez que el Motor de Comparacion
(Submodulo 5.1) detecta un cambio real en cargo, dependencia, correo,
telefono o area para una persona dentro de una entidad, la version
VIGENTE actual se CIERRA (`fecha_fin`) y se abre una nueva version
(`numero_version + 1`). Es la fuente de verdad para responder preguntas
como "¿Quien era Director Juridico en junio?" o "¿Desde cuando ocupa el
cargo?" (Submodulo 5.3), y para reconstruir cuando una persona cambio de
dependencia en el tiempo (Submodulo 5.4).

Distinta de `Funcionario` (Modulo 4): `Funcionario` es el PUNTERO al
vinculo vigente actual (una fila por persona+entidad activa, se actualiza
in-place por `PersistenciaInteligenteService`); `VersionFuncionario` es el
historial COMPLETO, append-only, de cada estado que ese vinculo tuvo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from govdata.domain.exceptions.domain_exceptions import VersionFuncionarioInvalidaError


class EstadoVersion(str, Enum):
    VIGENTE = "vigente"
    CERRADA = "cerrada"


@dataclass(slots=True)
class VersionFuncionario:
    """Una version (snapshot en el tiempo) del vinculo Persona-Entidad-Cargo."""

    persona_id: int
    entidad_id: int
    numero_version: int
    cargo: str
    dependencia: str
    area: str
    documento_id: int
    """Documento origen de ESTA version -- el que motivo su apertura."""
    fecha_inicio: date
    id: int | None = None
    funcionario_id: int | None = None
    correo: str | None = None
    telefono: str | None = None
    fecha_fin: date | None = None
    estado: EstadoVersion = EstadoVersion.VIGENTE
    creado_en: datetime | None = None

    def __post_init__(self) -> None:
        if self.numero_version < 1:
            raise VersionFuncionarioInvalidaError(f"numero_version invalido: {self.numero_version}")
        if not self.cargo or not self.cargo.strip():
            raise VersionFuncionarioInvalidaError("VersionFuncionario requiere cargo no vacio")
        if not self.dependencia or not self.dependencia.strip():
            raise VersionFuncionarioInvalidaError("VersionFuncionario requiere dependencia no vacia")
        if self.fecha_fin is not None and self.fecha_fin < self.fecha_inicio:
            raise VersionFuncionarioInvalidaError(
                f"fecha_fin ({self.fecha_fin}) no puede ser anterior a fecha_inicio ({self.fecha_inicio})"
            )
        if self.estado == EstadoVersion.VIGENTE and self.fecha_fin is not None:
            raise VersionFuncionarioInvalidaError("Una version VIGENTE no puede tener fecha_fin")
        if self.estado == EstadoVersion.CERRADA and self.fecha_fin is None:
            raise VersionFuncionarioInvalidaError("Una version CERRADA requiere fecha_fin")

    def cerrar(self, fecha_fin: date) -> None:
        """VIGENTE -> CERRADA. Se llama cuando el Motor de Comparacion
        detecta un cambio real y esta version deja de reflejar el estado
        actual de la persona."""
        if self.estado != EstadoVersion.VIGENTE:
            raise VersionFuncionarioInvalidaError(
                f"Solo una version VIGENTE puede cerrarse (estado actual: {self.estado.value})"
            )
        if fecha_fin < self.fecha_inicio:
            raise VersionFuncionarioInvalidaError(
                f"No se puede cerrar antes de fecha_inicio ({self.fecha_inicio})"
            )
        self.fecha_fin = fecha_fin
        self.estado = EstadoVersion.CERRADA

    @property
    def vigente(self) -> bool:
        return self.estado == EstadoVersion.VIGENTE
