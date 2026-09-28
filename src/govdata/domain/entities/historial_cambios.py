"""Entidad de dominio: HistorialCambios.

Registra cada transicion detectada en el cargo/dependencia/entidad de un
Funcionario a lo largo del tiempo (ej. "2026 Director Juridico" ->
"2027 Procurador"). Se genera cuando el pipeline de un mes detecta que un
`Funcionario` vigente ya no aparece con los mismos datos que en la corrida
anterior. La generacion activa de estos registros (comparando corridas
consecutivas) es responsabilidad de un caso de uso del modulo de
Orquestacion; aqui solo se define la forma y las invariantes del registro.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from govdata.domain.exceptions.domain_exceptions import GovDataError


class HistorialCambiosInvalidoError(GovDataError):
    """Un registro de HistorialCambios no cumple sus invariantes."""


@dataclass(slots=True)
class HistorialCambios:
    """Un cambio puntual detectado en la trayectoria de un Funcionario."""

    persona_id: int
    entidad_id: int
    campo_modificado: str  # ej. "cargo", "dependencia"
    valor_anterior: str | None
    valor_nuevo: str | None
    detectado_en: date
    id: int | None = None
    funcionario_id: int | None = None
    creado_en: datetime | None = None

    def __post_init__(self) -> None:
        if not self.campo_modificado or not self.campo_modificado.strip():
            raise HistorialCambiosInvalidoError(
                "HistorialCambios requiere campo_modificado no vacio"
            )
        if self.valor_anterior == self.valor_nuevo:
            raise HistorialCambiosInvalidoError(
                "HistorialCambios no puede registrar un cambio sin diferencia "
                f"real (campo='{self.campo_modificado}', valor='{self.valor_nuevo}')"
            )
        self.campo_modificado = self.campo_modificado.strip()
