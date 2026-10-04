"""Selectores centralizados para ConsultaEcuador.

Verificados contra el DOM real el 2026-10-02:
- URL: https://consultasecuador.com/en-linea/personas/consultar-cedula-con-nombres
- Método: GET
- Campos: apellidos (id="surname"), nombres (id="names")
- Resultados: tabla con cédula, nombre completo

Si el sitio cambia sus selectores, este es el UNICO archivo que deberia
requerir edicion. Ningun otro modulo del sistema hardcodea estos selectores.
"""

from __future__ import annotations

# URL del formulario de consulta
URL_CONSULTA = "https://consultasecuador.com/en-linea/personas/consultar-cedula-con-nombres"

# Selectores del formulario
SELECTOR_INPUT_APELLIDOS = "#surname"
SELECTOR_INPUT_NOMBRES = "#names"
SELECTOR_BOTON_CONSULTAR = "button[type='submit'], input[type='submit']"

# Selectores de resultados
SELECTOR_TABLA_RESULTADOS = "table"
SELECTOR_FILAS_RESULTADOS = "table tbody tr"
SELECTOR_CEDULA = "td:nth-child(1)"
SELECTOR_NOMBRE_COMPLETO = "td:nth-child(2)"

# Selectores de estado
SELECTOR_SIN_RESULTADOS = "text=No se encontraron resultados"
SELECTOR_CAPTCHA = "text=captcha, text=recaptcha, text=challenge"
SELECTOR_ERROR = "text=error, text=Error"
