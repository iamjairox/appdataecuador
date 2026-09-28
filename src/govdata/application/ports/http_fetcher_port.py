"""Puerto: HttpFetcherPort.

Ruta "ligera" del ScraperEngine (ver arquitectura general): cuando se
conoce una URL directa a un recurso (como los `url_documento` que
descubrio el Modulo 2), no tiene sentido levantar un navegador Playwright
completo para descargarlo. Este puerto define una descarga HTTP simple
(implementada con `requests` en infraestructura), usada por el Modulo 3
para materializar los documentos.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.application.dto.descarga_dto import RespuestaDescargaDTO


class HttpFetcherPort(ABC):
    """Descarga directa de un recurso via HTTP, sin motor de navegador."""

    @abstractmethod
    def descargar(self, url: str) -> RespuestaDescargaDTO:
        """Descarga el contenido completo de `url`.

        Debe lanzar excepciones de dominio segun el resultado (ver
        `domain.exceptions`): `RecursoNoDisponibleError` en 404/410,
        `DescargaFallidaError` en timeout/red/5xx/429. Nunca lanza
        excepciones de `requests` u otra libreria directamente -- ese
        mapeo es responsabilidad del adaptador.
        """
