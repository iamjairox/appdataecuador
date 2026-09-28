"""Caso de uso: DescargarDocumentoUseCase.

Descarga UN documento ya descubierto (Modulo 2), lo valida (HTTP, MIME,
magic bytes), calcula su huella (SHA-256, tamano), lo almacena
(deduplicando globalmente por hash) y deja rastro completo en `Descarga`
(el intento) y `Manifest` (el resultado canonico). Nunca parsea el
contenido -- eso es explicitamente responsabilidad de un modulo futuro.

Este caso de uso SI propaga excepciones (a diferencia de
`DescubrirEntidadUseCase` en el Modulo 2): es la pieza atomica; la
garantia de "nunca detener el pipeline completo" la da la capa que lo
invoca en bucle sobre la cola (`DescargaOrchestratorService`), no este
caso de uso en si mismo.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from govdata.application.ports.descarga_repository_port import DescargaRepositoryPort
from govdata.application.ports.documento_repository_port import DocumentoRepositoryPort
from govdata.application.ports.file_storage_port import FileStoragePort
from govdata.application.ports.http_fetcher_port import HttpFetcherPort
from govdata.application.ports.manifest_repository_port import ManifestRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.descarga import Descarga, EstadoDescarga
from govdata.domain.entities.documento import (
    DocumentoInvalidoError,
    DocumentoTransparencia,
    TipoArchivo,
)
from govdata.domain.entities.manifest import Manifest
from govdata.domain.exceptions.domain_exceptions import (
    ContenidoInvalidoError,
    DescargaFallidaError,
    DocumentoYaEnProcesoError,
    GovDataError,
    PresupuestoReintentosAgotadoError,
    RecursoNoDisponibleError,
)
from govdata.domain.rules.generador_ruta_almacenamiento import construir_ruta_almacenamiento
from govdata.domain.rules.validador_contenido_archivo import (
    es_pagina_error_html,
    mime_por_tipo,
    resolver_tipo_real,
)

logger = get_logger(__name__)

_BYTES_MAGIC = 512
_DURACION_MINIMA_SEGUNDOS = 1e-6  # evita division por cero en descargas instantaneas (tests)

_ERRORES_DESCARGA = (DescargaFallidaError, RecursoNoDisponibleError, ContenidoInvalidoError)


class DescargarDocumentoUseCase:
    """Descarga, valida, almacena y audita UN documento pendiente."""

    def __init__(
        self,
        http_fetcher: HttpFetcherPort,
        storage: FileStoragePort,
        documento_repository: DocumentoRepositoryPort,
        descarga_repository: DescargaRepositoryPort,
        manifest_repository: ManifestRepositoryPort,
        max_reintentos: int = 3,
    ) -> None:
        self._http_fetcher = http_fetcher
        self._storage = storage
        self._documento_repository = documento_repository
        self._descarga_repository = descarga_repository
        self._manifest_repository = manifest_repository
        self._max_reintentos = max_reintentos

    def ejecutar(self, documento: DocumentoTransparencia) -> DocumentoTransparencia:
        if documento.id is None:
            raise DocumentoInvalidoError("El documento requiere id para descargarse (persistalo primero)")

        intentos_previos = self._descarga_repository.contar_intentos(documento.id)
        if intentos_previos >= self._max_reintentos:
            raise PresupuestoReintentosAgotadoError(
                f"Documento {documento.id} agoto los {self._max_reintentos} intentos permitidos"
            )

        if not self._documento_repository.reclamar_para_descarga(documento.id):
            raise DocumentoYaEnProcesoError(f"Documento {documento.id} ya fue reclamado por otro worker")
        documento.iniciar_descarga()

        documento_id: int = documento.id
        numero_intento = intentos_previos + 1
        iniciado_en = datetime.now(UTC)

        try:
            return self._descargar_validar_y_almacenar(documento, documento_id, numero_intento, iniciado_en)
        except _ERRORES_DESCARGA as exc:
            self._registrar_fallo(documento, documento_id, numero_intento, iniciado_en, str(exc))
            raise

    def _descargar_validar_y_almacenar(
        self,
        documento: DocumentoTransparencia,
        documento_id: int,
        numero_intento: int,
        iniciado_en: datetime,
    ) -> DocumentoTransparencia:
        respuesta = self._http_fetcher.descargar(documento.url_documento)
        primeros_bytes = respuesta.contenido[:_BYTES_MAGIC]

        if es_pagina_error_html(respuesta.content_type, primeros_bytes):
            raise ContenidoInvalidoError(
                f"El servidor devolvio una pagina de error en vez del documento "
                f"(Content-Type={respuesta.content_type!r}, HTTP {respuesta.codigo_http})"
            )

        resultado_tipo = resolver_tipo_real(respuesta.content_type, primeros_bytes, documento.tipo_archivo)
        if resultado_tipo.tipo_detectado is None:
            raise ContenidoInvalidoError(
                f"No se pudo determinar el tipo real del contenido descargado "
                f"(Content-Type={respuesta.content_type!r})"
            )
        if not resultado_tipo.coincide_con_esperado:
            logger.warning(
                "tipo_real_no_coincide_con_esperado",
                documento_id=documento.id,
                tipo_esperado=documento.tipo_archivo.value,
                tipo_detectado=resultado_tipo.tipo_detectado.value,
                fuente_deteccion=resultado_tipo.fuente,
            )
        tipo_real = resultado_tipo.tipo_detectado

        hash_sha256 = hashlib.sha256(respuesta.contenido).hexdigest()
        tamano_bytes = len(respuesta.contenido)
        finalizado_en = datetime.now(UTC)
        duracion_segundos = max(
            (finalizado_en - iniciado_en).total_seconds(), _DURACION_MINIMA_SEGUNDOS
        )
        velocidad = tamano_bytes / duracion_segundos

        storage_uri = self._almacenar_con_deduplicacion(respuesta.contenido, hash_sha256, tipo_real)

        documento.completar_descarga(
            ruta_almacenamiento=storage_uri,
            hash_sha256=hash_sha256,
            tamano_bytes=tamano_bytes,
            descargado_en=finalizado_en,
            etag=respuesta.etag,
            last_modified=respuesta.last_modified,
        )
        documento_actualizado = self._documento_repository.guardar_o_actualizar(documento)

        self._descarga_repository.registrar(
            Descarga(
                documento_id=documento_id,
                numero_intento=numero_intento,
                estado=EstadoDescarga.EXITO,
                codigo_http=respuesta.codigo_http,
                content_type_recibido=respuesta.content_type,
                tamano_bytes=tamano_bytes,
                hash_sha256=hash_sha256,
                velocidad_bytes_por_segundo=velocidad,
                iniciado_en=iniciado_en,
                finalizado_en=finalizado_en,
            )
        )
        self._manifest_repository.registrar(
            Manifest(
                documento_id=documento_id,
                url=documento.url_documento,
                sha256=hash_sha256,
                mime=mime_por_tipo(tipo_real),
                bytes_totales=tamano_bytes,
                storage_uri=storage_uri,
                fecha_descarga=finalizado_en,
            )
        )

        logger.info(
            "documento_descargado",
            documento_id=documento_id,
            version=documento.version,
            tamano_bytes=tamano_bytes,
            velocidad_bytes_por_segundo=round(velocidad, 2),
            duracion_segundos=round(duracion_segundos, 3),
            hash_sha256=hash_sha256[:12],
        )
        return documento_actualizado

    def _almacenar_con_deduplicacion(
        self, contenido: bytes, hash_sha256: str, tipo_archivo: TipoArchivo
    ) -> str:
        manifest_existente = self._manifest_repository.buscar_por_hash(hash_sha256)
        if manifest_existente is not None:
            logger.info("contenido_deduplicado", hash_sha256=hash_sha256[:12])
            return manifest_existente.storage_uri

        ruta_relativa = construir_ruta_almacenamiento(hash_sha256, tipo_archivo)
        return self._storage.guardar(contenido, ruta_relativa)

    def _registrar_fallo(
        self,
        documento: DocumentoTransparencia,
        documento_id: int,
        numero_intento: int,
        iniciado_en: datetime,
        mensaje_error: str,
    ) -> None:
        finalizado_en = datetime.now(UTC)
        try:
            documento.marcar_error()
            self._documento_repository.guardar_o_actualizar(documento)
        except GovDataError:
            logger.error("no_se_pudo_marcar_documento_error", documento_id=documento_id)

        self._descarga_repository.registrar(
            Descarga(
                documento_id=documento_id,
                numero_intento=numero_intento,
                estado=EstadoDescarga.FALLO,
                mensaje_error=mensaje_error,
                iniciado_en=iniciado_en,
                finalizado_en=finalizado_en,
            )
        )
        logger.warning("descarga_fallida", documento_id=documento_id, error=mensaje_error)
