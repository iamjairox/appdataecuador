"""Tests de integracion: Container (DI) -- metodos del Modulo 3.

Mismo truco que `test_container.py`: se pre-carga `session_factory` en
el `__dict__` de la instancia para evitar PostgreSQL real.
"""

from __future__ import annotations

from sqlalchemy.orm import sessionmaker

from govdata.config.container import Container
from govdata.config.settings import Settings, reset_settings_cache
from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel
from govdata.infrastructure.storage.local_file_storage_adapter import LocalFileStorageAdapter
from govdata.infrastructure.storage.minio_storage_adapter import MinioStorageAdapter


def _container(
    sqlite_engine_multihilo, servidor_fixtures_descarga, directorio_storage_temporal, **overrides
) -> Container:
    valores = {
        "download": {
            "concurrencia_maxima": 2,
            "timeout_segundos": 2.0,
            "max_reintentos": 1,
            "backoff_base_segundos": 0.01,
        },
        "storage": {"backend": "local", "ruta_local": directorio_storage_temporal},
    }
    valores.update(overrides)
    settings = Settings(APP_ENV="test", **valores)
    container = Container(settings=settings)
    container.__dict__["session_factory"] = sessionmaker(bind=sqlite_engine_multihilo, future=True)
    return container


def test_storage_property_usa_backend_local(
    sqlite_engine_multihilo, servidor_fixtures_descarga, directorio_storage_temporal
) -> None:
    container = _container(sqlite_engine_multihilo, servidor_fixtures_descarga, directorio_storage_temporal)
    assert isinstance(container.storage, LocalFileStorageAdapter)
    assert container.storage is container.storage  # cached_property: misma instancia


def test_storage_property_usa_backend_minio(
    sqlite_engine_multihilo, servidor_fixtures_descarga, directorio_storage_temporal, monkeypatch
) -> None:
    monkeypatch.setattr("govdata.infrastructure.storage.minio_storage_adapter.Minio", lambda *a, **k: _MinioFalso())

    container = _container(
        sqlite_engine_multihilo,
        servidor_fixtures_descarga,
        directorio_storage_temporal,
        storage={"backend": "minio"},
    )
    assert isinstance(container.storage, MinioStorageAdapter)


class _MinioFalso:
    def bucket_exists(self, _bucket: str) -> bool:
        return True

    def make_bucket(self, _bucket: str) -> None:
        pass


def test_listar_documentos_pendientes(
    sqlite_engine_multihilo, servidor_fixtures_descarga, directorio_storage_temporal
) -> None:
    container = _container(sqlite_engine_multihilo, servidor_fixtures_descarga, directorio_storage_temporal)

    with container.nueva_sesion() as sesion:
        sesion.add(
            DocumentoModel(
                publicacion_id=1,
                tipo_archivo="pdf",
                nombre_original="d.pdf",
                url_documento=f"{servidor_fixtures_descarga.url_origen}/archivo/valido.pdf",
            )
        )

    pendientes = container.listar_documentos_pendientes()
    assert len(pendientes) == 1


def test_pipeline_descarga_extremo_a_extremo(
    sqlite_engine_multihilo, servidor_fixtures_descarga, directorio_storage_temporal
) -> None:
    container = _container(sqlite_engine_multihilo, servidor_fixtures_descarga, directorio_storage_temporal)

    with container.nueva_sesion() as sesion:
        sesion.add(
            DocumentoModel(
                publicacion_id=1,
                tipo_archivo="pdf",
                nombre_original="d.pdf",
                url_documento=f"{servidor_fixtures_descarga.url_origen}/archivo/valido.pdf",
            )
        )

    pendientes = container.listar_documentos_pendientes()
    orquestador = container.crear_pipeline_descarga()
    resumen = orquestador.ejecutar(pendientes)

    assert resumen.total_documentos == 1
    assert resumen.descargados == 1


def teardown_module() -> None:
    reset_settings_cache()
