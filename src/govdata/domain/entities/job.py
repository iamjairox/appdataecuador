"""Entidad de dominio: Job -- Submodulo 4.8 (Job Manager).

Cada consulta (individual, masiva o por filtros -- Submodulos 4.5/4.6/4.7)
genera un `Job` que rastrea su progreso end-to-end. `JobStep` (en
`job_step.py`) es el historial append-only de cada transicion de estado,
simetrico al patron ya usado para `Descarga`/`Ejecucion` en Modulos 2-3.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from govdata.domain.exceptions.domain_exceptions import GovDataError


class JobStatus(str, Enum):
    PENDIENTE = "pendiente"
    EN_COLA = "en_cola"
    DESCUBRIENDO = "descubriendo"
    DESCARGANDO = "descargando"
    EXTRAYENDO = "extrayendo"
    NORMALIZANDO = "normalizando"
    CLASIFICANDO = "clasificando"
    GUARDANDO = "guardando"
    CONSULTANDO_SENESCYT = "consultando_senescyt"
    CONSULTANDO_FORO = "consultando_foro"
    FINALIZADO = "finalizado"
    ERROR = "error"


class TipoJob(str, Enum):
    CONSULTA_INDIVIDUAL = "consulta_individual"
    CONSULTA_MASIVA = "consulta_masiva"
    CONSULTA_FILTROS = "consulta_filtros"


class JobInvalidoError(GovDataError):
    """Un Job no cumple sus invariantes."""


# Progreso indicativo (0-100) asociado a cada estado del pipeline -- usado
# por defecto si `JobManagerService` no recibe un porcentaje explicito.
PORCENTAJE_POR_ESTADO: dict[JobStatus, float] = {
    JobStatus.PENDIENTE: 0.0,
    JobStatus.EN_COLA: 5.0,
    JobStatus.DESCUBRIENDO: 15.0,
    JobStatus.DESCARGANDO: 30.0,
    JobStatus.EXTRAYENDO: 50.0,
    JobStatus.NORMALIZANDO: 65.0,
    JobStatus.CLASIFICANDO: 75.0,
    JobStatus.GUARDANDO: 90.0,
    JobStatus.CONSULTANDO_SENESCYT: 95.0,
    JobStatus.CONSULTANDO_FORO: 97.0,
    JobStatus.FINALIZADO: 100.0,
    JobStatus.ERROR: 100.0,
}


@dataclass(slots=True)
class Job:
    """Auditoria y progreso de una consulta end-to-end."""

    tipo: TipoJob
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    entidad_id: int | None = None
    estado: JobStatus = JobStatus.PENDIENTE
    porcentaje: float = 0.0
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    errores: list[str] = field(default_factory=list)
    reintentos: int = 0

    def __post_init__(self) -> None:
        if not 0.0 <= self.porcentaje <= 100.0:
            raise JobInvalidoError(f"porcentaje fuera de rango [0,100]: {self.porcentaje}")
        if self.reintentos < 0:
            raise JobInvalidoError(f"reintentos no puede ser negativo: {self.reintentos}")

    def transicionar(self, nuevo_estado: JobStatus, porcentaje: float | None = None) -> None:
        self.estado = nuevo_estado
        self.porcentaje = porcentaje if porcentaje is not None else PORCENTAJE_POR_ESTADO[nuevo_estado]

    def finalizar(self, fecha_fin: datetime) -> None:
        self.estado = JobStatus.FINALIZADO
        self.porcentaje = 100.0
        self.fecha_fin = fecha_fin

    def marcar_error(self, mensaje: str, fecha_fin: datetime) -> None:
        self.estado = JobStatus.ERROR
        self.errores.append(mensaje)
        self.fecha_fin = fecha_fin

    def registrar_reintento(self) -> None:
        self.reintentos += 1

    @property
    def duracion_segundos(self) -> float | None:
        if self.fecha_inicio is None or self.fecha_fin is None:
            return None
        return (self.fecha_fin - self.fecha_inicio).total_seconds()
