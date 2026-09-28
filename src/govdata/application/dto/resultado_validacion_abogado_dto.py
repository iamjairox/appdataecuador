"""Salida pública mínima de la validación; no contiene identificadores."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ResultadoDirectorioAutorizadoDTO:
    nombre: str
    puesto: str
    unidad: str
    ciudad: str | None
    telefono: str | None
    celular: str | None
    correo: str | None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)
