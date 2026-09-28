"""Value Object: Correo electronico."""

from __future__ import annotations

import re
from dataclasses import dataclass

from govdata.domain.exceptions.domain_exceptions import ValorInvalidoError

_PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class Correo:
    """Correo electronico validado y normalizado (minusculas, sin espacios)."""

    valor: str

    def __post_init__(self) -> None:
        normalizado = self.valor.strip().lower()
        if not _PATRON_CORREO.match(normalizado):
            raise ValorInvalidoError(f"Correo invalido: '{self.valor}'")
        object.__setattr__(self, "valor", normalizado)

    def __str__(self) -> str:
        return self.valor

    @classmethod
    def crear_opcional(cls, valor: str | None) -> Correo | None:
        """Crea un Correo si `valor` es no vacio y valido; retorna None en caso contrario.

        Los directorios institucionales frecuentemente tienen celdas vacias
        o con valores basura ('N/A', '-'); este metodo evita que eso tumbe
        el pipeline de extraccion.
        """
        if not valor or not valor.strip():
            return None
        try:
            return cls(valor)
        except ValorInvalidoError:
            return None
