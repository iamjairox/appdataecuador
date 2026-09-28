"""Puerto: FileStoragePort.

Abstrae el almacenamiento de archivos binarios (documentos descargados).
La implementacion de Foundation/Modulo 1 sera local (disco), pero el
contrato ya esta preparado para un adaptador MinIO/S3 sin cambiar una
sola linea de los casos de uso que lo consumen -- ese es exactamente el
punto de tener el puerto separado del adaptador.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class FileStoragePort(ABC):
    """Almacenamiento de archivos binarios (documentos fuente)."""

    @abstractmethod
    def guardar(self, contenido: bytes, ruta_relativa: str) -> str:
        """Guarda `contenido` y retorna la ruta/URI final de almacenamiento."""

    @abstractmethod
    def leer(self, ruta_relativa: str) -> bytes: ...

    @abstractmethod
    def existe(self, ruta_relativa: str) -> bool: ...
