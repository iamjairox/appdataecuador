"""Entidad de dominio: HistorialAcademico -- Submodulo 7.14 (Versionado:
"siempre conservar que cambio, cuando, quien, origen, fecha").

Distinta de `TituloVersionAcademica` (snapshot COMPLETO del estado de un
titulo en un momento dado): esta es la bitacora de CAMBIOS -- una fila por
diferencia real detectada por el Comparador Academico (7.7), con el
detalle campo a campo. Es lo que arma directamente la seccion "historial"
del contrato oficial (Submodulo 7.16) y responde "¿que cambio
exactamente?" sin tener que diffear dos versiones completas a mano.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from govdata.domain.exceptions.domain_exceptions import HistorialAcademicoInvalidoError
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico


@dataclass(slots=True)
class HistorialAcademico:
    """Un registro de cambio detectado sobre un titulo (o su alta/baja)."""

    persona_master_id: int
    clave_titulo: str
    tipo_cambio: TipoCambioAcademico
    detectado_en: datetime
    consulta_senescyt_id: int
    """`quien`: siempre el sistema (Submodulo 7.20: sin intervencion manual
    en Modulo 7) -- se deja como campo explicito por si un futuro flujo de
    correccion manual lo necesita."""
    ejecutado_por: str = "sistema"
    id: int | None = None
    titulo_academico_id: int | None = None
    campos_modificados: list[dict[str, Any]] = field(default_factory=list)
    descripcion: str | None = None

    def __post_init__(self) -> None:
        if self.persona_master_id is None:
            raise HistorialAcademicoInvalidoError("HistorialAcademico requiere persona_master_id")
        if self.tipo_cambio == TipoCambioAcademico.SIN_CAMBIOS:
            raise HistorialAcademicoInvalidoError(
                "No se registra HistorialAcademico para SIN_CAMBIOS (nunca reescribir sin motivo real)"
            )
