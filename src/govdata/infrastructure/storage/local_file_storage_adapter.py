"""Adaptador: LocalFileStorageAdapter."""

from __future__ import annotations

import os
from pathlib import Path

from govdata.application.ports.file_storage_port import FileStoragePort


class LocalFileStorageAdapter(FileStoragePort):
    """Almacenamiento en disco local, bajo un directorio base configurable."""

    def __init__(self, ruta_base: str) -> None:
        self._ruta_base = Path(ruta_base).resolve()
        self._ruta_base.mkdir(parents=True, exist_ok=True)

    def guardar(self, contenido: bytes, ruta_relativa: str) -> str:
        ruta_completa = self._resolver(ruta_relativa)
        ruta_completa.parent.mkdir(parents=True, exist_ok=True)
        ruta_completa.write_bytes(contenido)
        return f"file://{ruta_completa.as_posix()}"

    def leer(self, ruta_relativa: str) -> bytes:
        return self._resolver(ruta_relativa).read_bytes()

    def existe(self, ruta_relativa: str) -> bool:
        return self._resolver(ruta_relativa).exists()

    def _resolver(self, ruta_relativa: str) -> Path:
        """Resuelve `ruta_relativa` contra la base, rechazando cualquier
        intento de escapar del directorio base (path traversal)."""
        ruta = (self._ruta_base / ruta_relativa).resolve()
        if os.path.commonpath([str(self._ruta_base), str(ruta)]) != str(self._ruta_base):
            raise ValueError(f"ruta_relativa fuera del directorio base: '{ruta_relativa}'")
        return ruta
