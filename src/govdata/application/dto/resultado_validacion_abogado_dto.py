"""Salida pública de la validación de abogado; no contiene identificadores.

La cédula es únicamente una llave técnica transitoria y NUNCA aparece en
esta respuesta ni en ninguna superficie pública (API, frontend, logs,
exportaciones).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ResultadoDirectorioAutorizadoDTO:
    """Resultado de la validación de abogado, sin identificadores sensibles."""

    # Datos del funcionario
    nombre: str
    institucion: str
    cargo: str
    dependencia: str
    ciudad: str | None = None
    correo_institucional: str | None = None
    telefono_institucional: str | None = None
    celular: str | None = None

    # Estado de la validación
    estado_validacion: str = "pendiente"
    confianza: float | None = None

    # Información profesional obtenida (sin cédula)
    informacion_profesional: str | None = None
    fuente: str | None = None
    fecha_consulta: datetime | None = None

    def to_dict(self) -> dict:
        resultado = asdict(self)
        # Convertir datetime a string para JSON
        if self.fecha_consulta is not None:
            resultado["fecha_consulta"] = self.fecha_consulta.isoformat()
        return resultado
