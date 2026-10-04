"""Value Object: NombreCompleto.

Normaliza nombres y apellidos para que el futuro Motor de Identity
Resolution (comparacion entre fuentes: Transparencia, SENESCYT, Funcion
Judicial, etc.) trabaje siempre sobre texto consistente:

    "JUAN CARLOS PEREZ"   -> "JUAN CARLOS PEREZ"
    "Juan C. Perez"       -> "JUAN C PEREZ"
    "  perez   juan carlos " -> "PEREZ JUAN CARLOS"

Este value object SOLO normaliza (mayusculas, tildes fuera, espacios
colapsados, puntuacion fuera). La comparacion difusa entre distintas
fuentes (RapidFuzz + score de confianza) es responsabilidad de un
componente de dominio posterior (`IdentityResolutionPort`), fuera del
alcance del Modulo 1.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from govdata.domain.exceptions.domain_exceptions import ValorInvalidoError
from govdata.domain.rules.texto_humano import reparar_texto_humano


def _normalizar_texto(texto: str) -> str:
    # La huella elimina tildes por separado; aqui se conserva la grafia que
    # ve el usuario y que se envia a las fuentes externas.
    sin_puntuacion = re.sub(r"[.,;:]", " ", reparar_texto_humano(texto))
    colapsado = re.sub(r"\s+", " ", sin_puntuacion).strip()
    return colapsado.upper()


@dataclass(frozen=True, slots=True)
class NombreCompleto:
    """Nombres y apellidos de una persona, normalizados independientemente."""

    nombres: str
    apellidos: str

    def __post_init__(self) -> None:
        nombres_norm = _normalizar_texto(self.nombres)
        apellidos_norm = _normalizar_texto(self.apellidos)

        if not nombres_norm or not apellidos_norm:
            raise ValorInvalidoError(
                "NombreCompleto requiere nombres y apellidos no vacios "
                f"(nombres='{self.nombres}', apellidos='{self.apellidos}')"
            )

        object.__setattr__(self, "nombres", nombres_norm)
        object.__setattr__(self, "apellidos", apellidos_norm)

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"

    def __str__(self) -> str:
        return self.nombre_completo
