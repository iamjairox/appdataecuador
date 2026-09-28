"""Entidad de dominio: HistorialForo -- Submodulo 8.6 (Historial: "guardar
todas las versiones. Append Only").

Distinta de `RegistroForoVersion` (snapshot COMPLETO del estado en un
momento dado): esta es la bitacora de CAMBIOS -- una fila por diferencia
real detectada por el Comparador Foro (8.5), con el detalle campo a
campo. Mismo rol que `HistorialAcademico` (Modulo 7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from govdata.domain.exceptions.domain_exceptions import HistorialForoInvalidoError
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo


@dataclass(slots=True)
class HistorialForo:
    """Un registro de cambio detectado sobre un registro del Foro (o su
    alta/baja)."""

    persona_master_id: int
    clave_registro: str
    tipo_cambio: TipoCambioForo
    detectado_en: datetime
    consulta_foro_id: int
    """`quien`: siempre el sistema (Submodulo 8.18: sin intervencion
    manual) -- campo explicito por si un futuro flujo de correccion
    manual lo necesita."""
    ejecutado_por: str = "sistema"
    id: int | None = None
    registro_foro_id: int | None = None
    campos_modificados: list[dict[str, Any]] = field(default_factory=list)
    descripcion: str | None = None

    def __post_init__(self) -> None:
        if self.persona_master_id is None:
            raise HistorialForoInvalidoError("HistorialForo requiere persona_master_id")
        if self.tipo_cambio == TipoCambioForo.SIN_CAMBIOS:
            raise HistorialForoInvalidoError(
                "No se registra HistorialForo para SIN_CAMBIOS (nunca reescribir sin motivo real)"
            )
