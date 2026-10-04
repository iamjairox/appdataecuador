"""Detección de bloqueo anti-bot real (Cloudflare u interstitial).

Un widget reCAPTCHA embebido en un formulario operable NO se trata como
bloqueo: esas páginas siguen permitiendo la consulta.
"""

from __future__ import annotations

_MARCAS_BLOQUEO = (
    "just a moment",
    "checking your browser",
    "cf-browser-verification",
    "attention required",
    "enable javascript and cookies to continue",
    "verify you are human",
)


def pagina_bloqueada_por_antibot(contenido: str) -> bool:
    texto = contenido.lower()
    return any(marca in texto for marca in _MARCAS_BLOQUEO)
