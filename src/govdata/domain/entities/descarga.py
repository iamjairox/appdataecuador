"""Entidad de dominio: Descarga.

Registro de auditoria APPEND-ONLY de cada intento de descarga de un
Documento (exitoso o no). Mientras `Documento` solo refleja el estado
ACTUAL, `Descarga` acumula el historial completo: cuantos intentos hubo,
que codigo HTTP devolvio cada uno, cuanto tardo, a que velocidad, y el
mensaje de error si fallo. Es la base de la observabilidad exigida por el
Modulo 3 (tiempo, velocidad, tamano, hash, reintentos, errores, codigo
HTTP, Content-Type).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from govdata.domain.exceptions.domain_exceptions import GovDataError


class EstadoDescarga(str, Enum):
    EXITO = "exito"
    FALLO = "fallo"


class DescargaInvalidaError(GovDataError):
    """Un registro de Descarga no cumple sus invariantes."""


@dataclass(slots=True)
class Descarga:
    """Un intento (exitoso o fallido) de descargar un Documento."""

    documento_id: int
    numero_intento: int
    estado: EstadoDescarga
    iniciado_en: datetime
    finalizado_en: datetime
    id: int | None = None
    codigo_http: int | None = None
    content_type_recibido: str | None = None
    tamano_bytes: int | None = None
    hash_sha256: str | None = None
    velocidad_bytes_por_segundo: float | None = None
    mensaje_error: str | None = None

    def __post_init__(self) -> None:
        if self.numero_intento < 1:
            raise DescargaInvalidaError(f"numero_intento invalido: {self.numero_intento}")
        if self.finalizado_en < self.iniciado_en:
            raise DescargaInvalidaError("finalizado_en no puede ser anterior a iniciado_en")
        if self.estado == EstadoDescarga.EXITO and (
            self.tamano_bytes is None or self.hash_sha256 is None
        ):
            raise DescargaInvalidaError("Una Descarga EXITO requiere tamano_bytes y hash_sha256")
        if self.estado == EstadoDescarga.FALLO and not self.mensaje_error:
            raise DescargaInvalidaError("Una Descarga FALLO requiere mensaje_error")

    @property
    def duracion_segundos(self) -> float:
        return (self.finalizado_en - self.iniciado_en).total_seconds()
