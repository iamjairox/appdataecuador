"""Entidad de dominio: OportunidadComercial -- Submodulo 5.17.

"Preparar la plataforma para un futuro CRM... No implementar el CRM, solo
generar eventos estructurados" -- instruccion explicita del cliente. Se
genera cuando una diferencia detectada por el Motor de Comparacion (5.1)
coincide con un patron de interes comercial (nuevo Director Juridico,
nuevo Procurador, cambio de maxima autoridad, cambio masivo de
funcionarios). El futuro CRM, la API o el Dashboard consumiran esto via
`Evento` (5.7) -- esta entidad nunca envia nada por si misma.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from govdata.domain.exceptions.domain_exceptions import OportunidadComercialInvalidaError
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad


class TipoOportunidad(str, Enum):
    NUEVO_DIRECTOR_JURIDICO = "nuevo_director_juridico"
    NUEVO_PROCURADOR = "nuevo_procurador"
    NUEVO_DIRECTOR_FINANCIERO = "nuevo_director_financiero"
    CAMBIO_MAXIMA_AUTORIDAD_JURIDICA = "cambio_maxima_autoridad_juridica"
    CAMBIO_MASIVO_FUNCIONARIOS = "cambio_masivo_funcionarios"


@dataclass(slots=True)
class OportunidadComercial:
    """Un evento de negocio estructurado, candidato a un futuro CRM."""

    entidad_id: int
    tipo: TipoOportunidad
    descripcion: str
    detectado_en: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    persona_id: int | None = None
    prioridad: NivelCriticidad = NivelCriticidad.MEDIO

    def __post_init__(self) -> None:
        if not self.descripcion or not self.descripcion.strip():
            raise OportunidadComercialInvalidaError(
                f"OportunidadComercial (tipo={self.tipo.value}) requiere descripcion no vacia"
            )
        self.descripcion = self.descripcion.strip()
