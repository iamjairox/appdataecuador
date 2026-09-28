"""Mapper: DocumentoModel <-> DocumentoTransparencia (dominio)."""

from __future__ import annotations

from govdata.domain.entities.documento import DocumentoTransparencia
from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel


def a_dominio(modelo: DocumentoModel) -> DocumentoTransparencia:
    return DocumentoTransparencia(
        id=modelo.id,
        publicacion_id=modelo.publicacion_id,
        tipo_archivo=modelo.tipo_archivo,
        estado=modelo.estado,
        version=modelo.version,
        nombre_original=modelo.nombre_original,
        url_documento=modelo.url_documento,
        etag=modelo.etag,
        last_modified=modelo.last_modified,
        tamano_bytes=modelo.tamano_bytes,
        ruta_almacenamiento=modelo.ruta_almacenamiento,
        hash_sha256=modelo.hash_sha256,
        descubierto_en=modelo.descubierto_en,
        descargado_en=modelo.descargado_en,
        actualizado_en=modelo.actualizado_en,
    )


def a_modelo(documento: DocumentoTransparencia, modelo: DocumentoModel | None = None) -> DocumentoModel:
    modelo = modelo or DocumentoModel()
    if documento.id is not None:
        modelo.id = documento.id
    modelo.publicacion_id = documento.publicacion_id
    modelo.tipo_archivo = documento.tipo_archivo
    modelo.estado = documento.estado
    modelo.version = documento.version
    modelo.nombre_original = documento.nombre_original
    modelo.url_documento = documento.url_documento
    modelo.etag = documento.etag
    modelo.last_modified = documento.last_modified
    modelo.tamano_bytes = documento.tamano_bytes
    modelo.ruta_almacenamiento = documento.ruta_almacenamiento
    modelo.hash_sha256 = documento.hash_sha256
    modelo.descargado_en = documento.descargado_en
    return modelo
