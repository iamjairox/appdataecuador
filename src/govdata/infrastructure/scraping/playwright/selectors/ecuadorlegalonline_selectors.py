"""Selectores centralizados para EcuadorLegalOnline.

Verificados contra el DOM real el 2026-10-02:
- URL: https://www.ecuadorlegalonline.com/consultas/consultar-numero-cedula/
- Método: POST (formulario de WordPress)
- Campos: txtName (id="txtName") para apellidos y nombres
- Botón: btnNext (id="btnNext")
- Resultados: div con id="resultado"
- CAPTCHA: reCAPTCHA (iframe de Google)

Si el sitio cambia sus selectores, este es el UNICO archivo que deberia
requerir edicion. Ningun otro modulo del sistema hardcodea estos selectores.
"""

from __future__ import annotations

# URL del formulario de consulta
URL_CONSULTA = "https://www.ecuadorlegalonline.com/consultas/consultar-numero-cedula/"

# Selectores del formulario
SELECTOR_INPUT_NOMBRE = "#txtName"
SELECTOR_BOTON_CONSULTAR = "#btnNext"

# Selectores de resultados
SELECTOR_RESULTADO = "#resultado"
SELECTOR_TABLA_RESULTADOS = "#resultado table"
SELECTOR_FILAS_RESULTADOS = "#resultado table tbody tr"
SELECTOR_CEDULA = "td:nth-child(1)"
SELECTOR_NOMBRE_COMPLETO = "td:nth-child(2)"

# Selectores de estado
SELECTOR_SIN_RESULTADOS = "text=No se encontraron resultados"
SELECTOR_CAPTCHA = "iframe[src*='recaptcha'], .g-recaptcha, #captcha"
SELECTOR_ERROR = "text=error, text=Error, text=No se encontraron"
