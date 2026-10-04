"""Selectores centralizados para el Foro de Abogados de la Función Judicial.

Verificados contra el DOM real el 2026-09-28:
- URL: https://app.funcionjudicial.gob.ec/ForoAbogados/Login/frmCheckCodigoRegistro.jsp
- Método: POST
- Action: https://app.funcionjudicial.gob.ec/ForoAbogados/Abogado/frmGuardarAbogado.jsp
- Campo principal: CEDULA (id="CEDULA")
- Botón: btnValidarReg (id="btnValidarReg") con valor "Aceptar"

Si el sitio cambia sus selectores, este es el UNICO archivo que deberia
requerir edicion. Ningun otro modulo del sistema hardcodea estos selectores.
"""

from __future__ import annotations

# URL del formulario de consulta
URL_CONSULTA = "https://app.funcionjudicial.gob.ec/ForoAbogados/Login/frmCheckCodigoRegistro.jsp"

# Selectores del formulario
SELECTOR_INPUT_CEDULA = "#CEDULA"
SELECTOR_BOTON_ACEPTAR = "#btnValidarReg"

# Campos del resultado (ids del formulario real de Función Judicial)
SELECTOR_EMAIL = "#EMAIL"
SELECTOR_CELULAR = "#CELULAR"
SELECTOR_NOMBRES = "#NOMBRES"
SELECTOR_APELLIDOS = "#APELLIDOS"

# Selectores de resultados (la respuesta puede variar)
SELECTOR_TABLA_RESULTADOS = "table"
SELECTOR_FILAS_RESULTADOS = "table tbody tr"

# Selectores de estado
SELECTOR_SIN_RESULTADOS = "text=No se encontraron resultados, text=No existe"
SELECTOR_CAPTCHA = "text=captcha, text=recaptcha, text=challenge"
SELECTOR_ERROR = "text=error, text=Error"
