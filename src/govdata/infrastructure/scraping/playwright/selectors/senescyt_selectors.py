"""Selectores centralizados para SENESCYT (consulta de títulos por apellidos).

Verificados contra el DOM real el 2026-10-03:
- URL base (SIN jsessionid: el jsessionid es de sesion y lo asigna el
  servidor al navegar; nunca hardcodearlo):
  https://titulos-edusuperior.minedec.gob.ec/consulta-titulos-web/faces/vista/consulta/consulta.xhtml
- Formulario JSF `formPrincipal`:
  - apellidos (input id="formPrincipal:apellidos") -- UNICO campo
    necesario para la busqueda por apellidos
  - identificacion (input id="formPrincipal:identificacion")
  - captcha (img id="formPrincipal:capimg" + input
    id="formPrincipal:captchaSellerInput")
  - boton Buscar (id="formPrincipal:boton-buscar")

Si el sitio cambia sus selectores, este es el UNICO archivo que deberia
requerir edicion. Ningun otro modulo del sistema hardcodea estos selectores.
"""

from __future__ import annotations

# URL base del formulario de consulta (sin jsessionid).
URL_CONSULTA = (
    "https://titulos-edusuperior.minedec.gob.ec"
    "/consulta-titulos-web/faces/vista/consulta/consulta.xhtml"
)

# Selectores del formulario (los ":" de JSF se evitan con selector por atributo).
SELECTOR_INPUT_APELLIDOS = "[id='formPrincipal:apellidos']"
SELECTOR_INPUT_IDENTIFICACION = "[id='formPrincipal:identificacion']"
SELECTOR_BOTON_BUSCAR = "[id='formPrincipal:boton-buscar']"

# Selectores del captcha de imagen.
SELECTOR_CAPTCHA_IMG = "[id='formPrincipal:capimg']"
SELECTOR_CAPTCHA_INPUT = "[id='formPrincipal:captchaSellerInput']"

# Resultados: tabla JSF/PrimeFaces (estructura exacta por confirmar con una
# busqueda exitosa; el parser es tolerante y busca filas con cedula).
SELECTOR_TABLA_RESULTADOS = "table"
SELECTOR_FILAS_RESULTADOS = "table tbody tr"
