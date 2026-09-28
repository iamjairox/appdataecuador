"""Adaptador: DocumentoDescargaAdapter -- implementa `DescargaPort`.

Envuelve `DocumentoDescargaWorker` (Modulo 3), traduciendo su resultado
(`ResultadoDescargaDocumentoDTO`, que nunca lanza) al contrato de
`DescargaPort` (que SI lanza -- `ConsultaService` necesita saber si la
descarga fallo para decidir el estado del Job).
"""

from __future__ import annotations

from govdata.application.ports.descarga_port import DescargaPort
from govdata.domain.entities.documento import DocumentoTransparencia
from govdata.domain.exceptions.domain_exceptions import DescargaFallidaError
from govdata.infrastructure.http.documento_descarga_worker import DocumentoDescargaWorker


class DocumentoDescargaAdapter(DescargaPort):
    def __init__(self, worker: DocumentoDescargaWorker) -> None:
        self._worker = worker

    def descargar(self, documento: DocumentoTransparencia) -> DocumentoTransparencia:
        resultado = self._worker.procesar(documento)
        if not resultado.exito:
            raise DescargaFallidaError(resultado.error or f"Fallo la descarga del documento {documento.id}")
        return resultado.documento

    def cerrar(self) -> None:
        self._worker.cerrar()
