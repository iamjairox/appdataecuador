"""Adaptador: MinioStorageAdapter."""

from __future__ import annotations

import io

from minio import Minio
from minio.error import S3Error

from govdata.application.ports.file_storage_port import FileStoragePort
from govdata.domain.exceptions.domain_exceptions import PersistenciaError


class MinioStorageAdapter(FileStoragePort):
    """Almacenamiento en MinIO/S3, mismo contrato que el adaptador local."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        usar_ssl: bool = False,
        cliente: Minio | None = None,
    ) -> None:
        self._bucket = bucket
        # `cliente` inyectable para tests (doble de prueba del SDK de MinIO).
        self._cliente = cliente or Minio(
            endpoint, access_key=access_key, secret_key=secret_key, secure=usar_ssl
        )
        self._asegurar_bucket()

    def guardar(self, contenido: bytes, ruta_relativa: str) -> str:
        try:
            self._cliente.put_object(
                self._bucket,
                ruta_relativa,
                io.BytesIO(contenido),
                length=len(contenido),
            )
        except S3Error as exc:
            raise PersistenciaError(f"Fallo al guardar '{ruta_relativa}' en MinIO: {exc}") from exc
        return f"minio://{self._bucket}/{ruta_relativa}"

    def leer(self, ruta_relativa: str) -> bytes:
        respuesta = None
        try:
            respuesta = self._cliente.get_object(self._bucket, ruta_relativa)
            return respuesta.read()
        except S3Error as exc:
            raise PersistenciaError(f"Fallo al leer '{ruta_relativa}' de MinIO: {exc}") from exc
        finally:
            if respuesta is not None:
                respuesta.close()
                respuesta.release_conn()

    def existe(self, ruta_relativa: str) -> bool:
        try:
            self._cliente.stat_object(self._bucket, ruta_relativa)
            return True
        except S3Error:
            return False

    def _asegurar_bucket(self) -> None:
        try:
            if not self._cliente.bucket_exists(self._bucket):
                self._cliente.make_bucket(self._bucket)
        except S3Error as exc:
            raise PersistenciaError(f"No se pudo preparar el bucket '{self._bucket}': {exc}") from exc
