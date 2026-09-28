"""DTO: FuncionarioClasificadoDTO.

Salida del Clasificador Inteligente (Submodulo 4.3): una `FilaExtraidaDTO`
(ya normalizada) que SI pertenece a un area relevante, con el veredicto
de clasificacion adjunto. Las filas que no superan el umbral de confianza
nunca llegan a tener este DTO -- se descartan en el paso de clasificacion
(ver `ClasificadorFuncionariosService`).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from govdata.application.dto.fila_extraida_dto import FilaExtraidaDTO


class NivelConfianzaClasificacion(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


@dataclass(frozen=True, slots=True)
class FuncionarioClasificadoDTO:
    """Una fila clasificada como perteneciente a un area relevante."""

    fila: FilaExtraidaDTO
    area: str
    cargo_normalizado: str
    score: float
    nivel_confianza: NivelConfianzaClasificacion
    fingerprint: str | None = None
    fingerprint_hash: str | None = None

    def con_fingerprint(self, fingerprint: str, fingerprint_hash: str) -> FuncionarioClasificadoDTO:
        """Retorna una copia con el fingerprint de identidad ya calculado
        (Submodulo 4.4) -- los DTOs son inmutables, no se mutan in-place."""
        return replace(self, fingerprint=fingerprint, fingerprint_hash=fingerprint_hash)
