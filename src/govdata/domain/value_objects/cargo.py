"""Value Object: Cargo (nombre de puesto de trabajo, texto libre normalizado)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from govdata.domain.exceptions.domain_exceptions import ValorInvalidoError
from govdata.domain.rules.texto_humano import reparar_texto_humano


def _normalizar_texto(texto: str) -> str:
    colapsado = re.sub(r"\s+", " ", reparar_texto_humano(texto)).strip()
    return colapsado


@dataclass(frozen=True, slots=True)
class Cargo:
    """Denominacion de un cargo publico, tal como aparece en el directorio.

    Se conserva legible (Title Case) porque se muestra al usuario final;
    la comparacion difusa contra el catalogo de `AreaRelevante` se hace en
    mayusculas dentro del motor de clasificacion (modulo posterior).
    """

    valor: str

    def __post_init__(self) -> None:
        normalizado = _normalizar_texto(self.valor)
        if not normalizado:
            raise ValorInvalidoError(f"Cargo invalido: '{self.valor}'")
        object.__setattr__(self, "valor", normalizado.title())

    def __str__(self) -> str:
        return self.valor
