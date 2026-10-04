"""Selectores centralizados para SRI (Servicio de Rentas Internas).

Verificados contra el DOM real el 2026-10-04:
- URL: https://srienlinea.sri.gob.ec/sri-en-linea/SriPagosWeb/ConsultaDeudasFirmesImpugnadas/Consultas/consultaDeudasFirmesImpugnadas
- Pestaña activa: "Apellidos y nombres"
- Campo: input con placeholder "APELLIDOS NOMBRES"
- Botón: "Consultar"
- Resultado: tabla con RUC/cédula, razón social, estado

Si el sitio cambia sus selectores, este es el UNICO archivo que deberia
requerir edicion. Ningun otro modulo del sistema hardcodea estos selectores.
"""

from __future__ import annotations

# URL del formulario de consulta de deudas
URL_CONSULTA = "https://srienlinea.sri.gob.ec/sri-en-linea/SriPagosWeb/ConsultaDeudasFirmesImpugnadas/Consultas/consultaDeudasFirmesImpugnadas"

# Selectores del formulario
SELECTOR_INPUT_APELLIDOS_NOMBRES = "input[placeholder*='APELLIDOS NOMBRES']"
SELECTOR_BOTON_CONSULTAR = "button:has-text('Consultar')"

# Selectores de resultados
SELECTOR_TABLA_RESULTADOS = "table"
SELECTOR_FILAS_RESULTADOS = "table tbody tr"
SELECTOR_CEDULA = "td:nth-child(1)"
SELECTOR_NOMBRE = "td:nth-child(2)"

# Selectores de estado
SELECTOR_SIN_DEUDAS = "text=no registra deudas"
SELECTOR_CON_DEUDAS = "text=deudas"
