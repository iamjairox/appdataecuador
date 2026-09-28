"""Tests: DescargarDocumentoUseCase (con fakes, sin red ni BD real)."""

from __future__ import annotations

from pathlib import Path

import pytest

from govdata.application.dto.descarga_dto import RespuestaDescargaDTO
from govdata.application.use_cases.descargar_documento_use_case import DescargarDocumentoUseCase
from govdata.domain.entities.documento import (
    DocumentoInvalidoError,
    DocumentoTransparencia,
    EstadoDocumento,
    TipoArchivo,
)
from govdata.domain.exceptions.domain_exceptions import (
    ContenidoInvalidoError,
    DescargaFallidaError,
    DocumentoYaEnProcesoError,
    PresupuestoReintentosAgotadoError,
    RecursoNoDisponibleError,
)
from tests.unit.application.fakes_descarga import (
    FakeDescargaRepository,
    FakeDocumentoRepositoryDescarga,
    FakeFileStoragePort,
    FakeHttpFetcherPort,
    FakeManifestRepository,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "documentos"


def _bytes(nombre: str) -> bytes:
    return (FIXTURES / nombre).read_bytes()


def _documento(id_: int = 1, estado: EstadoDocumento = EstadoDocumento.DESCUBIERTO) -> DocumentoTransparencia:
    return DocumentoTransparencia(
        id=id_,
        publicacion_id=1,
        tipo_archivo=TipoArchivo.PDF,
        nombre_original="directorio.pdf",
        url_documento="https://x/directorio.pdf",
        estado=estado,
    )


def _caso_uso(
    http_fetcher: FakeHttpFetcherPort,
    documento: DocumentoTransparencia,
    storage: FakeFileStoragePort | None = None,
    descarga_repo: FakeDescargaRepository | None = None,
    manifest_repo: FakeManifestRepository | None = None,
    documento_repo: FakeDocumentoRepositoryDescarga | None = None,
    max_reintentos: int = 3,
) -> tuple[DescargarDocumentoUseCase, FakeFileStoragePort, FakeDescargaRepository, FakeManifestRepository]:
    storage = storage or FakeFileStoragePort()
    descarga_repo = descarga_repo or FakeDescargaRepository()
    manifest_repo = manifest_repo or FakeManifestRepository()
    documento_repo = documento_repo or FakeDocumentoRepositoryDescarga([documento])
    caso_uso = DescargarDocumentoUseCase(
        http_fetcher=http_fetcher,
        storage=storage,
        documento_repository=documento_repo,
        descarga_repository=descarga_repo,
        manifest_repository=manifest_repo,
        max_reintentos=max_reintentos,
    )
    return caso_uso, storage, descarga_repo, manifest_repo


class TestDescargaExitosa:
    def test_descarga_pdf_valido(self) -> None:
        documento = _documento()
        respuesta = RespuestaDescargaDTO(
            codigo_http=200,
            contenido=_bytes("directorio_valido.pdf"),
            content_type="application/pdf",
            etag='"abc123"',
            last_modified="Tue, 04 Aug 2026 10:00:00 GMT",
        )
        caso_uso, storage, descarga_repo, manifest_repo = _caso_uso(
            FakeHttpFetcherPort(respuesta=respuesta), documento
        )

        resultado = caso_uso.ejecutar(documento)

        assert resultado.estado == EstadoDocumento.DESCARGADO
        assert resultado.hash_sha256 is not None
        assert resultado.etag == '"abc123"'
        assert len(storage.archivos) == 1
        assert len(descarga_repo.registradas) == 1
        assert descarga_repo.registradas[0].estado.value == "exito"
        assert len(manifest_repo.registrados) == 1

    def test_detecta_xlsx_real(self) -> None:
        documento = _documento()
        documento.tipo_archivo = TipoArchivo.XLSX
        respuesta = RespuestaDescargaDTO(
            codigo_http=200,
            contenido=_bytes("directorio_valido.xlsx"),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            etag=None,
            last_modified=None,
        )
        caso_uso, *_ = _caso_uso(FakeHttpFetcherPort(respuesta=respuesta), documento)
        resultado = caso_uso.ejecutar(documento)
        assert resultado.estado == EstadoDocumento.DESCARGADO


class TestDeduplicacion:
    def test_contenido_duplicado_no_se_vuelve_a_almacenar(self) -> None:
        contenido = _bytes("directorio_valido.pdf")
        respuesta = RespuestaDescargaDTO(
            codigo_http=200, contenido=contenido, content_type="application/pdf", etag=None, last_modified=None
        )

        storage = FakeFileStoragePort()
        manifest_repo = FakeManifestRepository()
        descarga_repo = FakeDescargaRepository()

        doc1 = _documento(id_=1)
        caso_uso_1, *_ = _caso_uso(
            FakeHttpFetcherPort(respuesta=respuesta), doc1, storage, descarga_repo, manifest_repo
        )
        caso_uso_1.ejecutar(doc1)
        assert len(storage.archivos) == 1

        doc2 = _documento(id_=2)
        caso_uso_2, *_ = _caso_uso(
            FakeHttpFetcherPort(respuesta=respuesta), doc2, storage, descarga_repo, manifest_repo
        )
        resultado_2 = caso_uso_2.ejecutar(doc2)

        assert len(storage.archivos) == 1  # NO crecio: mismo contenido, mismo storage_uri
        assert len(manifest_repo.registrados) == 2  # pero SI se registro un manifest nuevo
        assert resultado_2.ruta_almacenamiento == manifest_repo.registrados[0].storage_uri


class TestErroresHttp:
    def test_404_marca_documento_error_y_propaga(self) -> None:
        documento = _documento()
        caso_uso, _, descarga_repo, _ = _caso_uso(
            FakeHttpFetcherPort(error_a_lanzar=RecursoNoDisponibleError("404")), documento
        )
        with pytest.raises(RecursoNoDisponibleError):
            caso_uso.ejecutar(documento)

        assert documento.estado == EstadoDocumento.ERROR
        assert descarga_repo.registradas[0].estado.value == "fallo"
        assert descarga_repo.registradas[0].mensaje_error is not None

    def test_500_propaga_descarga_fallida(self) -> None:
        documento = _documento()
        caso_uso, *_ = _caso_uso(
            FakeHttpFetcherPort(error_a_lanzar=DescargaFallidaError("Servidor respondio 500")), documento
        )
        with pytest.raises(DescargaFallidaError):
            caso_uso.ejecutar(documento)
        assert documento.estado == EstadoDocumento.ERROR

    def test_timeout_propaga_descarga_fallida(self) -> None:
        documento = _documento()
        caso_uso, *_ = _caso_uso(
            FakeHttpFetcherPort(error_a_lanzar=DescargaFallidaError("Timeout descargando")), documento
        )
        with pytest.raises(DescargaFallidaError, match="Timeout"):
            caso_uso.ejecutar(documento)


class TestContenidoInvalido:
    def test_pagina_de_error_disfrazada_de_pdf(self) -> None:
        documento = _documento()
        respuesta = RespuestaDescargaDTO(
            codigo_http=200,
            contenido=_bytes("pagina_error_disfrazada.pdf"),
            content_type="application/pdf",
            etag=None,
            last_modified=None,
        )
        caso_uso, _, descarga_repo, _ = _caso_uso(FakeHttpFetcherPort(respuesta=respuesta), documento)

        with pytest.raises(ContenidoInvalidoError):
            caso_uso.ejecutar(documento)

        assert documento.estado == EstadoDocumento.ERROR
        assert descarga_repo.registradas[0].estado.value == "fallo"

    def test_archivo_corrupto_sin_firma_reconocible(self) -> None:
        documento = _documento()
        respuesta = RespuestaDescargaDTO(
            codigo_http=200,
            contenido=_bytes("archivo_corrupto.bin"),
            content_type=None,
            etag=None,
            last_modified=None,
        )
        caso_uso, *_ = _caso_uso(FakeHttpFetcherPort(respuesta=respuesta), documento)
        with pytest.raises(ContenidoInvalidoError):
            caso_uso.ejecutar(documento)

    def test_tipo_real_distinto_al_esperado_se_acepta_con_advertencia(self) -> None:
        """Si el tipo real detectado es valido pero distinto al esperado
        (ej. la entidad publico PDF en vez del XLSX que decia la URL), se
        confia en el tipo REAL -- no se rechaza."""
        documento = _documento()
        documento.tipo_archivo = TipoArchivo.XLSX  # esperabamos XLSX...
        respuesta = RespuestaDescargaDTO(
            codigo_http=200,
            contenido=_bytes("directorio_valido.pdf"),  # ...pero es un PDF real
            content_type="application/pdf",
            etag=None,
            last_modified=None,
        )
        caso_uso, *_ = _caso_uso(FakeHttpFetcherPort(respuesta=respuesta), documento)
        resultado = caso_uso.ejecutar(documento)
        assert resultado.estado == EstadoDocumento.DESCARGADO


class TestColaYReintentos:
    def test_documento_ya_reclamado_por_otro_worker(self) -> None:
        documento = _documento()
        documento_repo = FakeDocumentoRepositoryDescarga([documento])
        documento_repo.reclamos_denegados.add(documento.id)  # type: ignore[arg-type]
        caso_uso, *_ = _caso_uso(FakeHttpFetcherPort(), documento, documento_repo=documento_repo)

        with pytest.raises(DocumentoYaEnProcesoError):
            caso_uso.ejecutar(documento)

    def test_presupuesto_de_reintentos_agotado(self) -> None:
        documento = _documento()
        descarga_repo = FakeDescargaRepository(intentos_previos=3)
        caso_uso, *_ = _caso_uso(
            FakeHttpFetcherPort(), documento, descarga_repo=descarga_repo, max_reintentos=3
        )
        with pytest.raises(PresupuestoReintentosAgotadoError):
            caso_uso.ejecutar(documento)

    def test_numero_de_intento_se_incrementa(self) -> None:
        documento = _documento()
        descarga_repo = FakeDescargaRepository(intentos_previos=1)
        respuesta = RespuestaDescargaDTO(
            codigo_http=200,
            contenido=_bytes("directorio_valido.pdf"),
            content_type="application/pdf",
            etag=None,
            last_modified=None,
        )
        caso_uso, *_ = _caso_uso(
            FakeHttpFetcherPort(respuesta=respuesta), documento, descarga_repo=descarga_repo
        )
        caso_uso.ejecutar(documento)
        assert descarga_repo.registradas[0].numero_intento == 2

    def test_documento_sin_id_lanza_error(self) -> None:
        documento = _documento(id_=None)  # type: ignore[arg-type]
        caso_uso, *_ = _caso_uso(FakeHttpFetcherPort(), documento)
        with pytest.raises(DocumentoInvalidoError):
            caso_uso.ejecutar(documento)
