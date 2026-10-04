"""Limpieza de texto mostrado o usado en consultas externas.

No confundir con ``normalizar_texto``: esa funcion elimina tildes para
comparar. Esta conserva la grafia humana y corrige errores de codificacion
frecuentes de documentos de Transparencia.
"""

from __future__ import annotations

import re
import unicodedata


# U+FFFD implica que el caracter se perdio antes de llegar a Python. Estas
# correcciones explicitas cubren terminos y apellidos recurrentes de DPE.
_CORRECCIONES_PERDIDAS = {
    "BU�AY": "BUÑAY", "T�CNICO": "TÉCNICO", "PLANIFICACI�N": "PLANIFICACIÓN",
    "PSIC�LOGA": "PSICÓLOGA", "CL�NICA": "CLÍNICA", "VEH�CULO": "VEHÍCULO",
    "DISE�ADOR": "DISEÑADOR", "ALBA�IL": "ALBAÑIL", "JOS�": "JOSÉ",
    "MAR�A": "MARÍA", "ANDR�S": "ANDRÉS", "DIRECCI�N": "DIRECCIÓN",
    "GESTI�N": "GESTIÓN", "COMUNICACI�N": "COMUNICACIÓN",
    "CONSTRUCCI�N": "CONSTRUCCIÓN", "ADMINISTRACI�N": "ADMINISTRACIÓN",
    "CEDE�O": "CEDEÑO", "CA�AVERAL": "CAÑAVERAL", "CARRE�O": "CARREÑO",
}


def _reparar_mojibake(texto: str) -> str:
    if not any(marca in texto for marca in ("Ã", "Â", "â")):
        return texto
    try:
        reparado = texto.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto
    return reparado if "�" not in reparado else texto


def reparar_texto_humano(texto: str | None) -> str:
    """Devuelve texto legible, NFC, conservando ñ y tildes.

    Si un reemplazo no puede inferirse, se retira solo el simbolo corrupto:
    es preferible a enviar ``�`` a Mis Datos Ecuador o al Foro.
    """
    if not texto:
        return ""
    limpio = unicodedata.normalize("NFC", _reparar_mojibake(texto)).replace("\x00", " ")
    for corrupto, correcto in _CORRECCIONES_PERDIDAS.items():
        limpio = re.sub(re.escape(corrupto), correcto, limpio, flags=re.IGNORECASE)
    limpio = re.sub(r"(?i)ACI�N", "ACIÓN", limpio)
    limpio = re.sub(r"(?i)CI�N", "CIÓN", limpio)
    limpio = re.sub(r"(?i)�A", "ÑA", limpio)
    limpio = re.sub(r"(?i)�O", "ÑO", limpio)
    limpio = re.sub(r"(?i)�I", "ÑI", limpio)
    limpio = re.sub(r"(?i)T�C", "TÉC", limpio)
    return re.sub(r"\s+", " ", limpio.replace("�", "")).strip()
