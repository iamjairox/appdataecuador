"""Puerto: PortalScraperPort.

Contrato que debe implementar cualquier adaptador capaz de navegar un
portal de transparencia gubernamental (DPE, y en el futuro SENESCYT,
Funcion Judicial, etc.) usando un motor de navegacion con JavaScript
(Playwright). Este puerto es "pesado" a proposito -- se reserva para
paginas que requieren interaccion real de navegador (SPAs client-side).

Principio de diseno: cada metodo retorna datos CRUDOS (DTOs), tal como el
portal los expone. Ninguna decision de negocio vive aqui:

    - "cual es el mes mas reciente publicado" -> `domain.rules.detector_ultimo_mes`
    - "cual numeral es el que buscamos"       -> `domain.rules.matcher_item_documento`
    - "que tipo de archivo es"                -> `domain.rules.detector_tipo_archivo`

Esto es lo que permite que el dominio se pruebe con datos en memoria, sin
Playwright, y que un portal nuevo (SENESCYT, Funcion Judicial) solo
requiera una nueva implementacion de este puerto reutilizando las mismas
reglas.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.application.dto.descubrimiento_dto import NumeralPublicadoDTO
from govdata.application.dto.entidad_dto import EntidadDescubiertaDTO


class PortalScraperPort(ABC):
    """Operaciones de navegacion sobre un portal de transparencia."""

    @abstractmethod
    def listar_entidades(self) -> list[EntidadDescubiertaDTO]:
        """Recorre el listado de entidades del portal y las retorna crudas."""

    @abstractmethod
    def listar_meses_publicados(self, url_entidad: str, anio: int) -> list[int]:
        """Retorna los numeros de mes (1-12) con publicaciones de
        Transparencia Activa para `anio`, o una lista vacia si no hay
        ninguna. No asume ninguna posicion fija: el llamador (caso de uso)
        decide como iterar anios hacia atras si la lista viene vacia.
        """

    @abstractmethod
    def listar_publicaciones_mes(
        self, url_entidad: str, anio: int, mes: int
    ) -> list[NumeralPublicadoDTO]:
        """Retorna todos los numerales publicados para ese anio/mes, con
        sus archivos adjuntos. NUNCA descarga el contenido de un archivo;
        solo su metadata (nombre, descripcion, url).
        """
