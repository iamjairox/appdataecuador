"""Selectores centralizados para Mis Datos Ecuador.

Verificados contra el DOM real el 2026-09-28:
- URL: https://misdatosecuador.com/consultas/personas/consultar-cedula-con-nombres.php
- Método: POST
- Campos: nombres (id="nombres"), apellidos (id="apellidos")
- Resultados: tabla con headers Cédula, Nombre completo, Edad

Si el sitio cambia sus selectores, este es el UNICO archivo que deberia
requerir edicion. Ningun otro modulo del sistema hardcodea estos selectores.
"""

from __future__ import annotations

# URL del formulario de consulta
URL_CONSULTA = "https://misdatosecuador.com/consultas/personas/consultar-cedula-con-nombres.php"

# Selectores del formulario
SELECTOR_INPUT_NOMBRES = "#nombres"
SELECTOR_INPUT_APELLIDOS = "#apellidos"
SELECTOR_BOTON_CONSULTAR = "button[type='submit'], input[type='submit']"

# Selectores de resultados
SELECTOR_TABLA_RESULTADOS = "table"
SELECTOR_FILAS_RESULTADOS = "table tbody tr"
SELECTOR_CEDULA = "td:nth-child(1)"
SELECTOR_NOMBRE_COMPLETO = "td:nth-child(2)"
SELECTOR_EDAD = "td:nth-child(3)"

# Selectores de estado
SELECTOR_SIN_RESULTADOS = "text=No se encontraron resultados"
SELECTOR_CAPTCHA = "text=captcha, text=recaptcha, text=challenge"
SELECTOR_ERROR = "text=error, text=Error"
