"""DTO: ResultadoConsultaEntidadDTO -- Submodulo 8.11, EL RESULTADO FINAL
cuando el usuario consulta una Entidad completa (ej. "Procuraduria General
del Estado"). Forma EXACTA pedida por el cliente:

    {"funcionarios": [...]}
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from govdata.application.dto.funcionario_consolidado_dto import FuncionarioConsolidadoDTO


@dataclass(frozen=True, slots=True)
class ResultadoConsultaEntidadDTO:
    funcionarios: list[FuncionarioConsolidadoDTO] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"funcionarios": [asdict(f) for f in self.funcionarios]}
