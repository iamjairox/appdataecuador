"""Regla de dominio: generador de fingerprint -- Submodulo 4.4 (Identity
Resolution, primera etapa).

Prepara la base para la resolucion de identidad entre fuentes (Modulo
SENESCYT/Funcion Judicial, futuro): construye una huella determinista a
partir de nombres y apellidos.

    "Juan Carlos" + "Pérez Gómez"
        -> quitar tildes, puntuacion, dobles espacios; mayusculas
        -> "JUAN CARLOS" + "PEREZ GOMEZ"
        -> concatenar sin espacios
        -> "JUANCARLOSPEREZGOMEZ"          (fingerprint)
        -> sha256(...)                      (fingerprint_hash)

Deliberadamente NO compara personas todavia (eso es la SEGUNDA etapa,
fuera del alcance del Modulo 4): esta regla solo produce la huella y su
hash de forma pura y determinista -- misma entrada, siempre la misma
salida, sin IO.

Conectores ("DE", "DEL", "LA", "LOS", "Y") se NORMALIZAN (mayuscula,
espaciado) pero NO se eliminan: quitarlos podria fusionar apellidos
distintos (ej. "DE LA CRUZ" vs "CRUZ"). Se documenta como decision
explicita, no como omision.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata


def _limpiar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    sin_puntuacion = re.sub(r"[.,;:'\"´`-]", " ", sin_tildes)
    colapsado = re.sub(r"\s+", " ", sin_puntuacion).strip()
    return colapsado.upper()


def generar_fingerprint(nombres: str, apellidos: str) -> tuple[str, str]:
    """Retorna `(fingerprint, fingerprint_hash)`.

    `fingerprint` es la huella legible (util para depuracion/logs);
    `fingerprint_hash` es su SHA-256 hexadecimal (clave compacta y
    determinista, apta para indexar en base de datos).
    """
    nombres_limpio = _limpiar(nombres).replace(" ", "")
    apellidos_limpio = _limpiar(apellidos).replace(" ", "")
    fingerprint = f"{nombres_limpio}{apellidos_limpio}"
    fingerprint_hash = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
    return fingerprint, fingerprint_hash
