"""Entidad de dominio: AtributoTrazable -- Submodulo 6.15 (Trazabilidad).

Cada dato consolidado en el perfil de una Persona debe poder responder:
¿quien lo obtuvo? ¿cuando? ¿de que fuente? ¿con que score? Esta entidad
es esa respuesta, un registro por (campo, valor) proveniente de una
fuente concreta -- lo que le permite al Motor de Fusion (Submodulo 6.14)
decidir, cuando dos fuentes reportan valores distintos para el mismo
campo, cual prevalece sin perder el dato descartado.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.exceptions.domain_exceptions import AtributoTrazableInvalidoError
from govdata.domain.value_objects.fuente_externa import FuenteExterna


@dataclass(slots=True)
class AtributoTrazable:
    """Procedencia de un unico campo consolidado del perfil de una Persona."""

    persona_master_id: int
    campo: str
    valor: str
    fuente: FuenteExterna
    obtenido_en: datetime
    score: float
    id: int | None = None
    registro_fuente_id: int | None = None

    def __post_init__(self) -> None:
        if self.persona_master_id is None:
            raise AtributoTrazableInvalidoError("AtributoTrazable requiere persona_master_id")
        if not self.campo or not self.campo.strip():
            raise AtributoTrazableInvalidoError("AtributoTrazable requiere campo no vacio")
        if not (0.0 <= self.score <= 100.0):
            raise AtributoTrazableInvalidoError(f"score fuera de rango [0, 100]: {self.score}")
        self.campo = self.campo.strip()
