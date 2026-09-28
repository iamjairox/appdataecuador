"""Smoke test funcional: pipeline de descarga end-to-end (Modulo 3).

Ejercita la cadena COMPLETA con componentes reales: `RequestsHttpFetcherAdapter`
real contra el servidor de fixtures local, `LocalFileStorageAdapter` con
I/O real de disco, repositorios SQLAlchemy reales contra SQLite. Solo el
portal remoto y PostgreSQL se sustituyen por sus equivalentes locales para
poder correr en CI sin red ni infraestructura externa.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import sessionmaker

from govdata.application.services.descarga_orchestrator_service import DescargaOrchestratorService
from govdata.application.use_cases.descargar_documento_use_case import DescargarDocumentoUseCase
from govdata.domain.entities.documento import DocumentoTransparencia, EstadoDocumento, TipoArchivo
from govdata.domain.exceptions.domain_exceptions import ContenidoInvalidoError
from govdata.infrastructure.http.documento_descarga_worker import DocumentoDescargaWorker
from govdata.infrastructure.http.requests_http_fetcher_adapter import RequestsHttpFetcherAdapter
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_descarga_repository import (
    SqlAlchemyDescargaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_documento_repository import (
    SqlAlchemyDocumentoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_manifest_repository import (
    SqlAlchemyManifestRepository,
)
from govdata.infrastructure.storage.local_file_storage_adapter import LocalFileStorageAdapter


def _persistir_documento(sesion, publicacion_id: int, url: str, tipo: TipoArchivo) -> DocumentoTransparencia:
    from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel

    modelo = DocumentoModel(
        publicacion_id=publicacion_id,
        tipo_archivo=tipo,
        estado=EstadoDocumento.DESCUBIERTO,
        version=1,
        nombre_original="directorio.pdf",
        url_documento=url,
    )
    sesion.add(modelo)
    sesion.flush()
    return SqlAlchemyDocumentoRepository(sesion).buscar_por_id(modelo.id)


def test_pipeline_completo_descarga_valida_almacena_y_audita(
    sesion, servidor_fixtures_descarga, directorio_storage_temporal
) -> None:
    documento = _persistir_documento(
        sesion, 1, f"{servidor_fixtures_descarga.url_origen}/archivo/valido.pdf", TipoArchivo.PDF
    )

    caso_uso = DescargarDocumentoUseCase(
        http_fetcher=RequestsHttpFetcherAdapter(timeout_segundos=5.0, max_reintentos=1),
        storage=LocalFileStorageAdapter(directorio_storage_temporal),
        documento_repository=SqlAlchemyDocumentoRepository(sesion),
        descarga_repository=SqlAlchemyDescargaRepository(sesion),
        manifest_repository=SqlAlchemyManifestRepository(sesion),
    )

    resultado = caso_uso.ejecutar(documento)
    sesion.flush()

    assert resultado.estado == EstadoDocumento.DESCARGADO
    assert resultado.hash_sha256 is not None
    assert resultado.tamano_bytes and resultado.tamano_bytes > 0

    manifests = SqlAlchemyManifestRepository(sesion).listar_por_documento(documento.id)
    assert len(manifests) == 1
    assert manifests[0].sha256 == resultado.hash_sha256

    descargas = SqlAlchemyDescargaRepository(sesion).listar_por_documento(documento.id)
    assert len(descargas) == 1
    assert descargas[0].estado.value == "exito"


def test_pipeline_completo_documento_invalido_queda_en_error(
    sesion, servidor_fixtures_descarga, directorio_storage_temporal
) -> None:
    documento = _persistir_documento(
        sesion,
        2,
        f"{servidor_fixtures_descarga.url_origen}/archivo/pagina-error-disfrazada",
        TipoArchivo.PDF,
    )

    caso_uso = DescargarDocumentoUseCase(
        http_fetcher=RequestsHttpFetcherAdapter(timeout_segundos=5.0, max_reintentos=1),
        storage=LocalFileStorageAdapter(directorio_storage_temporal),
        documento_repository=SqlAlchemyDocumentoRepository(sesion),
        descarga_repository=SqlAlchemyDescargaRepository(sesion),
        manifest_repository=SqlAlchemyManifestRepository(sesion),
    )

    with pytest.raises(ContenidoInvalidoError):
        caso_uso.ejecutar(documento)

    documento_final = SqlAlchemyDocumentoRepository(sesion).buscar_por_id(documento.id)
    assert documento_final.estado == EstadoDocumento.ERROR

    descargas = SqlAlchemyDescargaRepository(sesion).listar_por_documento(documento.id)
    assert descargas[0].estado.value == "fallo"


def test_orquestador_con_lote_mixto(
    sqlite_engine_multihilo, servidor_fixtures_descarga, directorio_storage_temporal
) -> None:
    """Lote de 3 documentos: 1 exitoso, 1 con 404, 1 con pagina de error --
    el orquestador reporta metricas correctas sin detenerse."""
    Factory = sessionmaker(bind=sqlite_engine_multihilo, future=True)
    sesion_setup = Factory()
    documentos = [
        _persistir_documento(
            sesion_setup, 1, f"{servidor_fixtures_descarga.url_origen}/archivo/valido.pdf", TipoArchivo.PDF
        ),
        _persistir_documento(
            sesion_setup,
            2,
            f"{servidor_fixtures_descarga.url_origen}/archivo/no-encontrado",
            TipoArchivo.PDF,
        ),
        _persistir_documento(
            sesion_setup,
            3,
            f"{servidor_fixtures_descarga.url_origen}/archivo/pagina-error-disfrazada",
            TipoArchivo.PDF,
        ),
    ]
    sesion_setup.commit()
    sesion_setup.close()

    storage = LocalFileStorageAdapter(directorio_storage_temporal)

    servicio = DescargaOrchestratorService(
        worker_factory=lambda: DocumentoDescargaWorker(
            session_factory=Factory,
            storage=storage,
            timeout_segundos=5.0,
            max_reintentos=1,
            backoff_base_segundos=0.05,
            tamano_maximo_bytes=None,
        ),
        concurrencia_maxima=2,
    )
    resumen = servicio.ejecutar(documentos)

    assert resumen.total_documentos == 3
    assert resumen.descargados == 1
    assert resumen.errores == 2
    assert resumen.bytes_totales > 0
