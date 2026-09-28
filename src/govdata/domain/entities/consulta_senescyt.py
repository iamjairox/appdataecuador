"""Entidad de dominio: ConsultaSenescyt -- Submodulo 7.15 (Auditoria).

Registra CADA intento de consulta a SENESCYT (exitoso o no), con detalle
especifico de esta fuente (mas rico que el `ConsultaFuenteLog` generico
del Modulo 6): respuesta cruda para trazabilidad/evidencia, si se sirvio
desde cache, y la version resultante del titulo afectado.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from govdata.domain.exceptions.domain_exceptions import ConsultaSenescytInvalidaError


@dataclass(slots=True)
class ConsultaSenescyt:
    """Un intento (exitoso o fallido) de consulta a SENESCYT para una PersonaMaster."""

    persona_master_id: int
    iniciado_en: datetime
    id: int | None = None
    finalizado_en: datetime | None = None
    exito: bool | None = None
    duracion_segundos: float | None = None
    error: str | None = None
    reintentos: int = 0
    cache_utilizado: bool = False
    version_resultante: int | None = None
    respuesta_cruda: dict[str, Any] | None = None
    """Evidencia (Submodulo 7.20, mejora 1): referencia cruda de lo que
    SENESCYT devolvio, para poder auditar de donde salio un dato."""

    def __post_init__(self) -> None:
        if self.persona_master_id is None:
            raise ConsultaSenescytInvalidaError("ConsultaSenescyt requiere persona_master_id")
        if self.reintentos < 0:
            raise ConsultaSenescytInvalidaError("reintentos no puede ser negativo")
        if self.finalizado_en is not None and self.finalizado_en < self.iniciado_en:
            raise ConsultaSenescytInvalidaError("finalizado_en no puede ser anterior a iniciado_en")

    def finalizar(
        self,
        exito: bool,
        cuando: datetime,
        duracion_segundos: float,
        error: str | None = None,
        version_resultante: int | None = None,
        respuesta_cruda: dict[str, Any] | None = None,
        cache_utilizado: bool = False,
    ) -> None:
        if cuando < self.iniciado_en:
            raise ConsultaSenescytInvalidaError("No se puede finalizar antes de iniciado_en")
        self.exito = exito
        self.finalizado_en = cuando
        self.duracion_segundos = duracion_segundos
        self.error = error
        self.version_resultante = version_resultante
        self.respuesta_cruda = respuesta_cruda
        self.cache_utilizado = cache_utilizado

    def registrar_reintento(self) -> None:
        self.reintentos += 1
