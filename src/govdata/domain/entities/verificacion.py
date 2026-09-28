"""Entidad de dominio: Verificacion -- Submodulos 5.10/5.15.

"Mantener un historial de verificaciones, incluso cuando no haya cambios"
-- instruccion explicita del cliente para el Motor de Monitoreo Continuo.
Cada vez que `MonitoreoContinuoService` evalua una entidad (con o sin
descarga real de por medio), queda un registro: o bien "se verifico el
hash remoto y no habia cambios" (nunca se descargo), o bien "se descargo,
se comparo, y el hash coincidia con el ya conocido" (Submodulo 5.10:
cache inteligente de comparacion). Es lo que permite responder "¿cuando
fue la ultima vez que se reviso esta entidad?" incluso en los meses donde
no paso nada.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.exceptions.domain_exceptions import VerificacionInvalidaError


@dataclass(slots=True)
class Verificacion:
    """Un chequeo puntual de vigencia/cambio para una entidad."""

    entidad_id: int
    hubo_cambio: bool
    motivo: str
    verificado_en: datetime
    id: int | None = None
    documento_id: int | None = None
    hash_verificado: str | None = None

    def __post_init__(self) -> None:
        if not self.motivo or not self.motivo.strip():
            raise VerificacionInvalidaError("Verificacion requiere motivo no vacio")
        self.motivo = self.motivo.strip()
