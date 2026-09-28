"""Entidad de dominio: Ejecucion (auditoria de una etapa del pipeline).

Un registro por cada intento de procesar una etapa (ej. "descubrimiento")
para una entidad, dentro de una corrida del pipeline. Es la base de datos
de la observabilidad del sistema: complementa (no reemplaza) al logging
estructurado -- los logs son para depurar en el momento, `Ejecucion` es
para poder consultar despues "que entidades fallaron la semana pasada y
por que", sin tener que grepear archivos de log.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from govdata.domain.exceptions.domain_exceptions import GovDataError


class EstadoEjecucion(str, Enum):
    EXITO = "exito"
    FALLO = "fallo"
    REINTENTO = "reintento"


class EjecucionInvalidaError(GovDataError):
    """Un registro de Ejecucion no cumple sus invariantes."""


@dataclass(slots=True)
class Ejecucion:
    """Auditoria de un intento de ejecutar una etapa del pipeline."""

    etapa: str
    estado: EstadoEjecucion
    iniciado_en: datetime
    id: int | None = None
    entidad_id: int | None = None
    mensaje_error: str | None = None
    intentos: int = 1
    finalizado_en: datetime | None = None

    def __post_init__(self) -> None:
        if not self.etapa or not self.etapa.strip():
            raise EjecucionInvalidaError("Ejecucion requiere una etapa no vacia")
        if self.intentos < 1:
            raise EjecucionInvalidaError(f"Ejecucion.intentos debe ser >= 1 (recibido {self.intentos})")
        if (
            self.finalizado_en is not None
            and self.finalizado_en < self.iniciado_en
        ):
            raise EjecucionInvalidaError("finalizado_en no puede ser anterior a iniciado_en")
        self.etapa = self.etapa.strip()

    @property
    def duracion_segundos(self) -> float | None:
        if self.finalizado_en is None:
            return None
        return (self.finalizado_en - self.iniciado_en).total_seconds()

    def finalizar(
        self, estado: EstadoEjecucion, finalizado_en: datetime, mensaje_error: str | None = None
    ) -> None:
        self.estado = estado
        self.finalizado_en = finalizado_en
        self.mensaje_error = mensaje_error
