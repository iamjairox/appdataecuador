"""Entidad de dominio: Funcionario.

Vincula una Persona con una Entidad publica en un Cargo, durante un rango
de tiempo determinado (fecha_inicio / fecha_fin). Este es el modelo N:M
en el tiempo que reemplaza al antiguo modelo "funcionarios" plano: la
misma Persona puede tener varios registros de Funcionario (uno por
entidad, o varios en el tiempo dentro de la misma entidad si cambia de
cargo), y todos apuntan al mismo `persona_id`.

Cuando `fecha_fin` es None, el vinculo se considera vigente (la persona
sigue ocupando ese cargo segun la ultima publicacion procesada).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from govdata.domain.exceptions.domain_exceptions import FuncionarioInvalidoError
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.cargo import Cargo


@dataclass(slots=True)
class Funcionario:
    """Vinculo Persona-Entidad-Cargo, con vigencia temporal."""

    persona_id: int
    entidad_id: int
    cargo: Cargo
    dependencia: str
    area_clasificada: AreaRelevante
    id: int | None = None
    score_clasificacion: float | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    documento_id: int | None = None
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None

    def __post_init__(self) -> None:
        if self.persona_id is None:
            raise FuncionarioInvalidoError("Funcionario requiere persona_id")
        if self.entidad_id is None:
            raise FuncionarioInvalidoError("Funcionario requiere entidad_id")
        if not self.dependencia or not self.dependencia.strip():
            raise FuncionarioInvalidoError(
                f"Funcionario (persona_id={self.persona_id}) requiere dependencia"
            )
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise FuncionarioInvalidoError(
                "fecha_fin no puede ser anterior a fecha_inicio "
                f"({self.fecha_fin} < {self.fecha_inicio})"
            )
        if self.score_clasificacion is not None and not (0.0 <= self.score_clasificacion <= 100.0):
            raise FuncionarioInvalidoError(
                f"score_clasificacion fuera de rango [0, 100]: {self.score_clasificacion}"
            )
        self.dependencia = self.dependencia.strip()

    @property
    def vigente(self) -> bool:
        return self.fecha_fin is None

    def finalizar(self, fecha_fin: date) -> None:
        """Cierra la vigencia de este cargo (la persona ya no lo ocupa)."""
        if self.fecha_inicio and fecha_fin < self.fecha_inicio:
            raise FuncionarioInvalidoError(
                f"No se puede finalizar antes de fecha_inicio ({self.fecha_inicio})"
            )
        self.fecha_fin = fecha_fin
