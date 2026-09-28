"""Parser HTML del Foro de Abogados -- Submodulo 8.4.

"Extraer UNICAMENTE los datos disponibles del Foro. Nunca inventar
informacion." Deliberadamente tolerante a DOS formas de marcado HTML
distintas (porque "no se asume aun como responde el Foro", mismo espiritu
que el Submodulo 7.2 con SENESCYT):

    1. Tablas: `<tr><td>Etiqueta</td><td>Valor</td></tr>` (o `<th>`).
    2. Pares etiqueta/valor sueltos: `<strong>Etiqueta:</strong> Valor`
       (o `<b>`/`<label>`), tipicamente dentro de un `<li>`/`<p>`/`<div>`.

Cualquier etiqueta que el catalogo (`CatalogoCamposForo`, Submodulo 8.3)
no reconozca se descarta silenciosamente -- nunca se inventa un campo, y
un cambio de HTML que agregue una fila nueva nunca rompe el parser."""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.domain.rules.normalizador_foro import normalizar_etiqueta_campo
from govdata.domain.rules.reglas_foro import CatalogoCamposForo

_CAMPOS_DTO = frozenset({"nombre_completo", "registro", "provincia", "estado", "cedula"})


def _desde_tablas(soup: BeautifulSoup, catalogo: CatalogoCamposForo) -> dict[str, str]:
    campos: dict[str, str] = {}
    for fila in soup.find_all("tr"):
        celdas = fila.find_all(["td", "th"])
        if len(celdas) < 2:
            continue
        etiqueta = celdas[0].get_text(strip=True)
        valor = celdas[1].get_text(strip=True)
        campo = normalizar_etiqueta_campo(etiqueta, catalogo)
        if campo in _CAMPOS_DTO and valor:
            campos.setdefault(campo, valor)
    return campos


def _desde_pares_sueltos(soup: BeautifulSoup, catalogo: CatalogoCamposForo) -> dict[str, str]:
    campos: dict[str, str] = {}
    for marcador in soup.find_all(["strong", "b", "label"]):
        etiqueta_texto = marcador.get_text(strip=True)
        campo = normalizar_etiqueta_campo(etiqueta_texto, catalogo)
        if campo is None or campo not in _CAMPOS_DTO:
            continue

        contenedor = marcador.parent
        if not isinstance(contenedor, Tag):
            continue
        texto_completo = contenedor.get_text(" ", strip=True)
        valor = texto_completo.replace(etiqueta_texto, "", 1).strip(" : ")
        if valor:
            campos.setdefault(campo, valor)
    return campos


def parsear_registro_foro(html: str, catalogo: CatalogoCamposForo) -> RegistroForoDTO | None:
    """Retorna `None` cuando no se reconocio NINGUN campo (pagina sin el
    perfil buscado -- "sin resultados" es una respuesta valida, no un
    error; ver `ForoAbogadosAdapter` para la deteccion de pagina
    verdaderamente vacia/invalida, que es un caso distinto y anterior a
    este parser)."""
    soup = BeautifulSoup(html, "html.parser")

    campos = _desde_tablas(soup, catalogo)
    for campo, valor in _desde_pares_sueltos(soup, catalogo).items():
        campos.setdefault(campo, valor)

    if not campos:
        return None

    return RegistroForoDTO(
        nombre_completo=campos.get("nombre_completo"), registro=campos.get("registro"),
        provincia=campos.get("provincia"), estado=campos.get("estado"), cedula=campos.get("cedula"),
    )
