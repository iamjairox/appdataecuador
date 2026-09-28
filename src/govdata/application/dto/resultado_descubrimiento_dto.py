"""DTO: ResultadoDescubrimientoEntidadDTO."""

from __future__ import annotations

from dataclasses import dataclass

from govdata.domain.entities.documento import DocumentoTransparencia
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.publicacion import PublicacionMensual


@dataclass(frozen=True, slots=True)
class ResultadoDescubrimientoEntidadDTO:
    """Resultado del descubrimiento completo para UNA entidad.

    `exito=False` con `error` poblado significa "se continuo con la
    siguiente entidad" (nunca se interrumpe el pipeline completo por una
    falla individual) -- ver `DescubrirEntidadUseCase`.
    """

    entidad: Entidad
    publicacion: PublicacionMensual | None
    documento: DocumentoTransparencia | None
    exito: bool
    error: str | None = None
