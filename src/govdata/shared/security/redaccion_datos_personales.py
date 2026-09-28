"""Evita que identificadores numéricos (cédulas) lleguen a superficies auditables.

La cédula es únicamente una llave técnica transitoria para resolver identidad
y consultar el registro profesional. NO debe:
- aparecer en frontend
- aparecer en CSV/Excel exportado
- almacenarse en logs
- almacenarse en errores
- incluirse en URLs registradas
- incluirse en auditoría textual
- aparecer en respuestas públicas de la API

Si temporalmente debe existir en memoria para realizar la siguiente consulta,
se elimina del flujo una vez terminada.
"""

from __future__ import annotations

import re

# Patrón para detectar cédulas de 10 dígitos (sin otros dígitos adyacentes)
_CEDULA = re.compile(r"(?<!\d)\d{10}(?!\d)")

# Marcador de redacción
_MARCADOR_REDACTADO = "[IDENTIFICADOR_REDACTADO]"


def redactar_cedulas(texto: str) -> str:
    """Redacta todas las cédulas de 10 dígitos en un texto.

    Uso:
        - Logs
        - Respuestas de API
        - Exportaciones (CSV/Excel)
        - Mensajes de excepción
        - URLs registradas
        - Auditoría textual
    """
    return _CEDULA.sub(_MARCADOR_REDACTADO, texto)


def sanitizar_error_externo(error: BaseException | str) -> str:
    """Redacta cédulas de un mensaje de error o excepción.

    Esta función se usa en los adaptadores para redactar cédulas de los
    mensajes de error antes de registrarlos en logs o propagarlos.
    """
    return redactar_cedulas(str(error))


def contiene_cedula(texto: str) -> bool:
    """Verifica si un texto contiene una cédula de 10 dígitos."""
    return bool(_CEDULA.search(texto))


def validar_sin_cedula(texto: str, contexto: str = "") -> None:
    """Lanza una excepción si el texto contiene una cédula.

    Útil para verificar que una respuesta de API o exportación no contiene
    cédulas antes de enviarla al usuario.
    """
    if contiene_cedula(texto):
        raise ValueError(
            f"El texto contiene una cédula y no debería. Contexto: {contexto}"
        )
