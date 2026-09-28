"""DTO: ResultadoParseoDTO.

Resultado de intentar extraer una `TablaExtraidaDTO` de un documento.
`REQUIERE_OCR` NO es un error: es un resultado legitimo -- un PDF
escaneado (sin capa de texto) se detecta y se marca para el futuro
Modulo de OCR, nunca se procesa a la fuerza ni se descarta en silencio.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO


class EstadoParseo(str, Enum):
    EXITO = "exito"
    REQUIERE_OCR = "requiere_ocr"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ResultadoParseoDTO:
    """Resultado de `DocumentParserPort.extraer()`."""

    estado: EstadoParseo
    tabla: TablaExtraidaDTO | None = None
    mensaje: str | None = None

    @property
    def exito(self) -> bool:
        return self.estado == EstadoParseo.EXITO
