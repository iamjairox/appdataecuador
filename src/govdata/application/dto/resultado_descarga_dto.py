"""DTO: ResultadoDescargaDocumentoDTO."""

from __future__ import annotations

from dataclasses import dataclass

from govdata.domain.entities.documento import DocumentoTransparencia


@dataclass(frozen=True, slots=True)
class ResultadoDescargaDocumentoDTO:
    """Resultado de procesar UN documento de la cola de descarga.

    `omitido=True` significa "no era un fallo real": otro worker ya lo
    habia reclamado, o ya agoto su presupuesto de reintentos -- en ambos
    casos simplemente se pasa al siguiente documento, sin contarlo como
    error en las metricas del orquestador.
    """

    documento: DocumentoTransparencia
    exito: bool
    omitido: bool = False
    error: str | None = None
