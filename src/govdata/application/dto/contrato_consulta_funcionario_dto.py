"""DTO: ContratoConsultaFuncionarioDTO -- Submodulo 8.16, EL CONTRATO
OFICIAL de una consulta individual (Submodulo 8.12) sobre un funcionario
puntual.

Forma EXACTA pedida por el cliente:

    {
      "entidad": "",
      "documento": "",
      "funcionario": {},
      "senescyt": {},
      "foro": {}
    }

`documento` es el numero de cedula del funcionario consultado (el
"documento de identidad" que amarra las 3 fuentes -- Transparencia,
SENESCYT, Foro). Nunca romper este contrato -- mismo criterio que
`PerfilAcademicoDTO` (Modulo 7, Submodulo 7.16)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ContratoConsultaFuncionarioDTO:
    """`{"entidad": "", "documento": "", "funcionario": {}, "senescyt":
    {}, "foro": {}}`."""

    entidad: str
    documento: str
    funcionario: dict[str, Any] = field(default_factory=dict)
    senescyt: dict[str, Any] = field(default_factory=dict)
    foro: dict[str, Any] = field(default_factory=dict)
    generado_en: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        return asdict(self)
