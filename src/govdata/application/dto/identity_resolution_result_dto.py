"""DTOs: resultado del Motor de Resolucion de Identidad (Submodulo 6.2).

`IdentityResolutionResultDTO` es el contrato de salida explicitamente
pedido: "persona encontrada, score, explicacion, motivo, campos
utilizados". `nivel_confianza` es puramente DESCRIPTIVO (para logs/
reportes humanos) -- la decision real de que hacer con el score (fusionar,
revisar, mantener separado) es responsabilidad exclusiva del Motor de
Confianza y Revision Manual (Submodulo 6.21, `motor_confianza_fusion.py`),
para no tener dos sistemas de umbrales compitiendo por la misma decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CampoUtilizadoDTO:
    """Como aporto UN campo individual al score compuesto."""

    campo: str
    valor_a: str | None
    valor_b: str | None
    coincide: bool
    score_campo: float
    peso: float
    aporte: float


@dataclass(frozen=True, slots=True)
class IdentityResolutionResultDTO:
    persona_master_id: int | None
    score: float
    nivel_confianza: str
    explicacion: str
    motivo: str
    campos_utilizados: list[CampoUtilizadoDTO] = field(default_factory=list)
