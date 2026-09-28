"""Mapper: DescargaModel <-> Descarga (dominio)."""

from __future__ import annotations

from govdata.domain.entities.descarga import Descarga
from govdata.infrastructure.persistence.postgresql.models.descarga_model import DescargaModel


def a_dominio(modelo: DescargaModel) -> Descarga:
    return Descarga(
        id=modelo.id,
        documento_id=modelo.documento_id,
        numero_intento=modelo.numero_intento,
        estado=modelo.estado,
        codigo_http=modelo.codigo_http,
        content_type_recibido=modelo.content_type_recibido,
        tamano_bytes=modelo.tamano_bytes,
        hash_sha256=modelo.hash_sha256,
        velocidad_bytes_por_segundo=modelo.velocidad_bytes_por_segundo,
        mensaje_error=modelo.mensaje_error,
        iniciado_en=modelo.iniciado_en,
        finalizado_en=modelo.finalizado_en,
    )


def a_modelo(descarga: Descarga) -> DescargaModel:
    return DescargaModel(
        id=descarga.id,
        documento_id=descarga.documento_id,
        numero_intento=descarga.numero_intento,
        estado=descarga.estado,
        codigo_http=descarga.codigo_http,
        content_type_recibido=descarga.content_type_recibido,
        tamano_bytes=descarga.tamano_bytes,
        hash_sha256=descarga.hash_sha256,
        velocidad_bytes_por_segundo=descarga.velocidad_bytes_por_segundo,
        mensaje_error=descarga.mensaje_error,
        iniciado_en=descarga.iniciado_en,
        finalizado_en=descarga.finalizado_en,
    )
