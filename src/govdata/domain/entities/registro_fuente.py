"""Entidad de dominio: RegistroFuente -- Submodulo 6.9 (Versionado por
Fuente).

Cada respuesta de una fuente externa (o de DPE, la fuente 0) para una
PersonaMaster se guarda como una version nueva -- "nunca sobreescribir".
`vigente=True` marca la version mas reciente; todas las anteriores quedan
`vigente=False` pero jamas se borran (Submodulo 6.15, trazabilidad).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from govdata.domain.exceptions.domain_exceptions import RegistroFuenteInvalidoError
from govdata.domain.value_objects.fuente_externa import FuenteExterna


@dataclass(slots=True)
class RegistroFuente:
    """Snapshot versionado de lo que una fuente reporto sobre una Persona."""

    persona_master_id: int
    fuente: FuenteExterna
    version: int
    datos: dict[str, Any] = field(default_factory=dict)
    consultado_en: datetime | None = None
    id: int | None = None
    vigente: bool = True
    hash_contenido: str | None = None

    def __post_init__(self) -> None:
        if self.persona_master_id is None:
            raise RegistroFuenteInvalidoError("RegistroFuente requiere persona_master_id")
        if self.version < 1:
            raise RegistroFuenteInvalidoError(f"version invalida (debe ser >= 1): {self.version}")
        if not self.datos:
            raise RegistroFuenteInvalidoError("RegistroFuente requiere al menos un dato")

    def cerrar(self) -> None:
        """La siguiente version reemplaza a esta como la vigente."""
        self.vigente = False
