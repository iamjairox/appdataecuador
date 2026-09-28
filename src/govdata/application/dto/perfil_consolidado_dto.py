"""DTO: PerfilConsolidadoDTO -- Submodulo 8.10, EL VERDADERO OBJETIVO DEL
SISTEMA.

Forma EXACTA pedida por el cliente:

    {
      "persona": {},
      "transparencia": {},
      "senescyt": {},
      "foro": {}
    }

Mejora arquitectonica adoptada a partir de este modulo (sugerida por el
cliente en el cierre del Modulo 8): el sistema deja de girar en torno a
"que fuente estoy consultando" y pasa a girar en torno al "Perfil Unico
del Funcionario". Este DTO es la materializacion de esa idea -- agrupa lo
que YA calcularon los pipelines de Transparencia (Modulos 1-5, `Persona`/
`Funcionario`), SENESCYT (Modulo 7, `PerfilAcademicoDTO`) y Foro de
Abogados (Modulo 8), sin recalcular nada. Cuando aparezca una fuente
nueva (Funcion Judicial, Contraloria, SERCOP, ...), el UNICO cambio en
este contrato es agregar una clave mas -- identidad, cache, comparacion,
historial, alertas y perfil consolidado permanecen intactos."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class PerfilConsolidadoDTO:
    """`{"persona": {}, "transparencia": {}, "senescyt": {}, "foro": {}}`."""

    persona: dict[str, Any]
    transparencia: dict[str, Any] = field(default_factory=dict)
    senescyt: dict[str, Any] = field(default_factory=dict)
    foro: dict[str, Any] = field(default_factory=dict)
    generado_en: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        """Serializacion exacta del contrato (para logging/API/n8n futuros)."""
        return asdict(self)
