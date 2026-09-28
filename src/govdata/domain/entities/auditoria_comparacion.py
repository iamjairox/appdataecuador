"""Entidad de dominio: AuditoriaComparacion -- Submodulo 5.9 (Auditoria).

Registra CADA ejecucion del Motor de Comparacion (exitosa o fallida):
quien la ejecuto, sobre que documento y version, cuando, cuanto tardo, y
cuantos cambios detecto. Simetrico al patron ya usado en `Ejecucion`
(Modulo 2) y `Descarga` (Modulo 3) -- append-only, una fila por corrida.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from govdata.domain.exceptions.domain_exceptions import AuditoriaComparacionInvalidaError


@dataclass(slots=True)
class AuditoriaComparacion:
    """Un registro de auditoria de UNA ejecucion de comparacion de documentos."""

    entidad_id: int
    documento_id: int
    version_documento: int
    ejecutado_por: str
    iniciado_en: datetime
    id: int | None = None
    finalizado_en: datetime | None = None
    duracion_segundos: float | None = None
    cambios_detectados: int = 0
    errores: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.ejecutado_por or not self.ejecutado_por.strip():
            raise AuditoriaComparacionInvalidaError("AuditoriaComparacion requiere ejecutado_por no vacio")
        if self.version_documento < 1:
            raise AuditoriaComparacionInvalidaError(f"version_documento invalida: {self.version_documento}")

    def finalizar(self, finalizado_en: datetime, cambios_detectados: int) -> None:
        self.finalizado_en = finalizado_en
        self.cambios_detectados = cambios_detectados
        self.duracion_segundos = (finalizado_en - self.iniciado_en).total_seconds()

    def marcar_error(self, mensaje: str, finalizado_en: datetime) -> None:
        self.errores.append(mensaje)
        self.finalizado_en = finalizado_en
        self.duracion_segundos = (finalizado_en - self.iniciado_en).total_seconds()
