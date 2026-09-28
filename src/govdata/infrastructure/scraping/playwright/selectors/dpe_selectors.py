"""Constantes especificas del portal DPE, centralizadas en un solo lugar.

Si el portal cambia sus rutas de API o su estructura, este es el UNICO
archivo que deberia requerir edicion (junto con las fixtures de test).
Ningun otro modulo del sistema hardcodea estas rutas.

Los paths corresponden a endpoints publicos, no autenticados, que la
propia aplicacion React del portal consume al renderizarse (verificado
manualmente el 2026-08-04 inspeccionando el trafico de red del sitio
real). Se acceden via `BrowserContext.request` de Playwright: siguen
siendo peticiones hechas por el navegador (comparten cookies/headers del
contexto), no una integracion "por fuera" del navegador.
"""

from __future__ import annotations

# Texto visible del acordeon "Transparencia activa" en la ficha de una
# entidad. Se conserva por si un futuro fallback DOM lo necesita (no se usa
# en el flujo principal, que es 100% via los endpoints JSON de abajo).
TEXTO_ACORDEON_TRANSPARENCIA_ACTIVA = "Transparencia activa"

RUTA_LISTADO_ENTIDADES = "/backend/v1/admin/public/establishment/list"
RUTA_MESES_PUBLICADOS = "/backend/v1/transparency/transparency/months"
RUTA_PUBLICACIONES_MES = "/backend/v1/transparency/transparency/active/public"

# type=A corresponde a "Transparencia Activa" (verificado: A/F/C se
# corresponden con Activa/Focalizada/Colaborativa en la UI).
TIPO_TRANSPARENCIA_ACTIVA = "A"
