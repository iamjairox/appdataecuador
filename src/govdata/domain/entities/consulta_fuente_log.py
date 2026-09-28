"""Entidad de dominio: ConsultaFuenteLog -- Submodulo 6.10 (Historial de
Consultas).

Registra CADA intento de consulta a una fuente externa (exitoso o no):
fecha, duracion, reintentos, error -- independiente de si produjo un
`RegistroFuente` nuevo. Es lo que le permite al Motor de Priorizacion
(6.11) y al Cache por Fuente (6.8) responder "¿cuando fue la ultima vez
que intentamos esto?" sin depender de si hubo datos o no.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.exceptions.domain_exceptions import ConsultaFuenteLogInvalidoError
from govdata.domain.value_objects.fuente_externa import FuenteExterna


@dataclass(slots=True)
class ConsultaFuenteLog:
    """Un intento (exitoso o fallido) de consulta a una fuente externa."""

    persona_master_id: int
    fuente: FuenteExterna
    iniciado_en: datetime
    id: int | None = None
    finalizado_en: datetime | None = None
    exito: bool | None = None
    duracion_segundos: float | None = None
    reintentos: int = 0
    error: str | None = None

    def __post_init__(self) -> None:
        if self.persona_master_id is None:
            raise ConsultaFuenteLogInvalidoError("ConsultaFuenteLog requiere persona_master_id")
        if self.reintentos < 0:
            raise ConsultaFuenteLogInvalidoError("reintentos no puede ser negativo")
        if self.finalizado_en is not None and self.finalizado_en < self.iniciado_en:
            raise ConsultaFuenteLogInvalidoError("finalizado_en no puede ser anterior a iniciado_en")

    def finalizar(
        self, exito: bool, cuando: datetime, duracion_segundos: float, error: str | None = None
    ) -> None:
        if cuando < self.iniciado_en:
            raise ConsultaFuenteLogInvalidoError("No se puede finalizar antes de iniciado_en")
        self.exito = exito
        self.finalizado_en = cuando
        self.duracion_segundos = duracion_segundos
        self.error = error
