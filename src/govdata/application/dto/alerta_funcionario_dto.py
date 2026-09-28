"""DTO: AlertaFuncionarioDTO -- Modulo 10 (API REST), `GET
/funcionarios/{persona_master_id}/alertas`.

Forma UNIFICADA de las 3 fuentes de alertas por `persona_master_id` que
YA EXISTEN, cada una en su propio modulo congelado -- `AlertaPerfil`
(Modulo 6, identidad), `AlertaAcademica` (Modulo 7, SENESCYT), `AlertaForo`
(Modulo 8, Foro de Abogados). Ningun servicio existente las junta; este
es exactamente el caso que la especificacion anticipa ("crea un caso de
uso nuevo en Modulo 10") -- `fuente` conserva de donde vino cada una,
nunca se pierde trazabilidad (Submodulo 10.30)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AlertaFuncionarioDTO:
    id: str
    fuente: str
    """`"identidad"` (Modulo 6) | `"academico"` (Modulo 7) | `"foro"` (Modulo 8)."""
    tipo: str
    prioridad: str
    descripcion: str
    detectado_en: datetime
    estado: str

    def to_dict(self) -> dict:
        return asdict(self)
