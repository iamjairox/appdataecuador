"""Puerto: DescargaWorkerPort.

Simetrico a `EntidadWorkerPort` (Modulo 2): abstrae "todo lo necesario
para descargar UN documento" (sesion HTTP, sesion de base de datos, casos
de uso) detras de un unico metodo, para que
`DescargaOrchestratorService` (application layer) reparta trabajo entre
hilos sin conocer `requests` ni SQLAlchemy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.application.dto.resultado_descarga_dto import ResultadoDescargaDocumentoDTO
from govdata.domain.entities.documento import DocumentoTransparencia


class DescargaWorkerPort(ABC):
    """Procesa la descarga completa de un documento, de principio a fin."""

    @abstractmethod
    def procesar(self, documento: DocumentoTransparencia) -> ResultadoDescargaDocumentoDTO: ...

    @abstractmethod
    def cerrar(self) -> None:
        """Libera recursos del worker (sesion HTTP, sesion de BD, etc.)."""
