"""Value Object: Telefono."""

from __future__ import annotations

import re
from dataclasses import dataclass

from govdata.domain.exceptions.domain_exceptions import ValorInvalidoError

# Acepta digitos, espacios, guiones, parentesis y un '+' opcional al inicio.
# La normalizacion final deja solo digitos (y un '+' inicial si existia).
_PATRON_PERMITIDO = re.compile(r"^\+?[\d\s\-()]{6,20}$")


@dataclass(frozen=True, slots=True)
class Telefono:
    """Numero de telefono validado y normalizado (solo digitos, + opcional)."""

    valor: str

    def __post_init__(self) -> None:
        crudo = self.valor.strip()
        if not _PATRON_PERMITIDO.match(crudo):
            raise ValorInvalidoError(f"Telefono invalido: '{self.valor}'")

        tiene_prefijo = crudo.startswith("+")
        solo_digitos = re.sub(r"\D", "", crudo)
        if len(solo_digitos) < 6:
            raise ValorInvalidoError(f"Telefono invalido: '{self.valor}'")

        normalizado = f"+{solo_digitos}" if tiene_prefijo else solo_digitos
        object.__setattr__(self, "valor", normalizado)

    def __str__(self) -> str:
        return self.valor

    @classmethod
    def crear_opcional(cls, valor: str | None) -> Telefono | None:
        """Crea un Telefono si `valor` es valido; retorna None en caso contrario."""
        if not valor or not valor.strip():
            return None
        try:
            return cls(valor)
        except ValorInvalidoError:
            return None
