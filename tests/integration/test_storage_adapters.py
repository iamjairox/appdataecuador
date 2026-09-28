"""Tests de integracion: adaptadores de storage.

`LocalFileStorageAdapter` se prueba con I/O real de disco (directorio
temporal). `MinioStorageAdapter` se prueba con el cliente `minio.Minio`
MOCKEADO -- no se requiere un servidor MinIO real corriendo para la
suite; se prueba el CONTRATO (que adaptador llama al SDK correctamente,
mapea errores, arma el `storage_uri`), no el SDK de MinIO en si.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from minio.error import S3Error

from govdata.domain.exceptions.domain_exceptions import PersistenciaError
from govdata.infrastructure.storage.local_file_storage_adapter import LocalFileStorageAdapter
from govdata.infrastructure.storage.minio_storage_adapter import MinioStorageAdapter


class TestLocalFileStorageAdapter:
    def test_guardar_y_leer(self, directorio_storage_temporal) -> None:
        adapter = LocalFileStorageAdapter(directorio_storage_temporal)
        uri = adapter.guardar(b"contenido de prueba", "ab/ab123.pdf")

        assert uri.startswith("file://")
        assert adapter.existe("ab/ab123.pdf") is True
        assert adapter.leer("ab/ab123.pdf") == b"contenido de prueba"

    def test_no_existe_antes_de_guardar(self, directorio_storage_temporal) -> None:
        adapter = LocalFileStorageAdapter(directorio_storage_temporal)
        assert adapter.existe("no/existe.pdf") is False

    def test_crea_subdirectorios_automaticamente(self, directorio_storage_temporal) -> None:
        adapter = LocalFileStorageAdapter(directorio_storage_temporal)
        adapter.guardar(b"x", "a1/b2/c3/archivo.pdf")
        assert adapter.existe("a1/b2/c3/archivo.pdf") is True

    def test_rechaza_path_traversal(self, directorio_storage_temporal) -> None:
        adapter = LocalFileStorageAdapter(directorio_storage_temporal)
        with pytest.raises(ValueError):
            adapter.guardar(b"malicioso", "../../../etc/passwd")

    def test_sobreescritura_idempotente_mismo_contenido(self, directorio_storage_temporal) -> None:
        adapter = LocalFileStorageAdapter(directorio_storage_temporal)
        uri1 = adapter.guardar(b"contenido", "ab/ab123.pdf")
        uri2 = adapter.guardar(b"contenido", "ab/ab123.pdf")
        assert uri1 == uri2


class TestMinioStorageAdapter:
    def _cliente_mock(self, bucket_existe: bool = True) -> MagicMock:
        cliente = MagicMock()
        cliente.bucket_exists.return_value = bucket_existe
        return cliente

    def test_crea_bucket_si_no_existe(self) -> None:
        cliente = self._cliente_mock(bucket_existe=False)
        MinioStorageAdapter(
            endpoint="localhost:9000",
            access_key="x",
            secret_key="y",
            bucket="documentos",
            cliente=cliente,
        )
        cliente.make_bucket.assert_called_once_with("documentos")

    def test_no_crea_bucket_si_ya_existe(self) -> None:
        cliente = self._cliente_mock(bucket_existe=True)
        MinioStorageAdapter(
            endpoint="localhost:9000", access_key="x", secret_key="y", bucket="documentos", cliente=cliente
        )
        cliente.make_bucket.assert_not_called()

    def test_guardar_arma_storage_uri_minio(self) -> None:
        cliente = self._cliente_mock()
        adapter = MinioStorageAdapter(
            endpoint="localhost:9000", access_key="x", secret_key="y", bucket="documentos", cliente=cliente
        )
        uri = adapter.guardar(b"contenido", "ab/ab123.pdf")

        assert uri == "minio://documentos/ab/ab123.pdf"
        cliente.put_object.assert_called_once()
        args, _kwargs = cliente.put_object.call_args
        assert args[0] == "documentos"
        assert args[1] == "ab/ab123.pdf"

    def test_guardar_mapea_s3error_a_persistencia_error(self) -> None:
        cliente = self._cliente_mock()
        cliente.put_object.side_effect = S3Error(
            code="InternalError",
            message="fallo",
            resource="x",
            request_id="1",
            host_id="1",
            response=MagicMock(),
        )
        adapter = MinioStorageAdapter(
            endpoint="localhost:9000", access_key="x", secret_key="y", bucket="documentos", cliente=cliente
        )
        with pytest.raises(PersistenciaError):
            adapter.guardar(b"contenido", "ab/ab123.pdf")

    def test_existe_true_cuando_stat_object_no_lanza(self) -> None:
        cliente = self._cliente_mock()
        adapter = MinioStorageAdapter(
            endpoint="localhost:9000", access_key="x", secret_key="y", bucket="documentos", cliente=cliente
        )
        assert adapter.existe("ab/ab123.pdf") is True

    def test_existe_false_cuando_stat_object_lanza(self) -> None:
        cliente = self._cliente_mock()
        cliente.stat_object.side_effect = S3Error(
            code="NoSuchKey",
            message="no existe",
            resource="x",
            request_id="1",
            host_id="1",
            response=MagicMock(),
        )
        adapter = MinioStorageAdapter(
            endpoint="localhost:9000", access_key="x", secret_key="y", bucket="documentos", cliente=cliente
        )
        assert adapter.existe("ab/ab123.pdf") is False

    def test_leer_retorna_contenido(self) -> None:
        cliente = self._cliente_mock()
        respuesta_mock = MagicMock()
        respuesta_mock.read.return_value = b"contenido leido"
        cliente.get_object.return_value = respuesta_mock

        adapter = MinioStorageAdapter(
            endpoint="localhost:9000", access_key="x", secret_key="y", bucket="documentos", cliente=cliente
        )
        assert adapter.leer("ab/ab123.pdf") == b"contenido leido"
        respuesta_mock.close.assert_called_once()
        respuesta_mock.release_conn.assert_called_once()
