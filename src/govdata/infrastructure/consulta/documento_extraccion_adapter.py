"""Adaptador: DocumentoExtraccionAdapter -- implementa `ExtraccionPort`.

Resuelve una ruta LOCAL de filesystem a partir de `Documento.ruta_almacenamiento`
(que puede ser `file://...` -- ya local -- o `minio://bucket/clave` --
hace falta bajarlo a un archivo temporal, porque `camelot`/`openpyxl`/
`xlrd` necesitan una ruta real de disco, no un stream de bytes) antes de
invocar `ExtraerDocumentoUseCase`.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from govdata.application.dto.resultado_unificado_dto import ResultadoUnificadoDTO
from govdata.application.ports.extraccion_port import ExtraccionPort
from govdata.application.ports.file_storage_port import FileStoragePort
from govdata.application.use_cases.extraer_documento_use_case import ExtraerDocumentoUseCase
from govdata.domain.entities.documento import DocumentoTransparencia
from govdata.domain.entities.entidad import Entidad
from govdata.domain.exceptions.domain_exceptions import ExtraccionFallidaError


class DocumentoExtraccionAdapter(ExtraccionPort):
    def __init__(self, caso_uso: ExtraerDocumentoUseCase, storage: FileStoragePort) -> None:
        self._caso_uso = caso_uso
        self._storage = storage

    def extraer(
        self, entidad: Entidad, documento: DocumentoTransparencia, mes_publicado: date
    ) -> ResultadoUnificadoDTO:
        if not documento.ruta_almacenamiento:
            raise ExtraccionFallidaError(f"Documento {documento.id} no tiene ruta_almacenamiento")

        with self._resolver_ruta_local(documento.ruta_almacenamiento) as ruta_local:
            return self._caso_uso.ejecutar(entidad, documento, ruta_local, mes_publicado)

    @contextmanager
    def _resolver_ruta_local(self, storage_uri: str) -> Iterator[str]:
        if storage_uri.startswith("file://"):
            yield storage_uri[len("file://") :]
            return

        clave_relativa = self._clave_desde_uri(storage_uri)
        contenido = self._storage.leer(clave_relativa)
        sufijo = Path(clave_relativa).suffix
        descriptor, ruta_temporal = tempfile.mkstemp(suffix=sufijo)
        try:
            with os.fdopen(descriptor, "wb") as archivo_temporal:
                archivo_temporal.write(contenido)
            yield ruta_temporal
        finally:
            os.remove(ruta_temporal)

    @staticmethod
    def _clave_desde_uri(storage_uri: str) -> str:
        """`minio://bucket/ab/hash.pdf` -> `ab/hash.pdf` (el bucket queda
        en `netloc`, `urlparse` ya lo separa del path)."""
        return urlparse(storage_uri).path.lstrip("/")
