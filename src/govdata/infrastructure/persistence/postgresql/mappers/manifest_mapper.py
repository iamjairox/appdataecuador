"""Mapper: ManifestModel <-> Manifest (dominio)."""

from __future__ import annotations

from govdata.domain.entities.manifest import Manifest
from govdata.infrastructure.persistence.postgresql.models.manifest_model import ManifestModel


def a_dominio(modelo: ManifestModel) -> Manifest:
    return Manifest(
        id=modelo.id,
        documento_id=modelo.documento_id,
        url=modelo.url,
        sha256=modelo.sha256,
        mime=modelo.mime,
        bytes_totales=modelo.bytes_totales,
        storage_uri=modelo.storage_uri,
        fecha_descarga=modelo.fecha_descarga,
    )


def a_modelo(manifest: Manifest) -> ManifestModel:
    return ManifestModel(
        id=manifest.id,
        documento_id=manifest.documento_id,
        url=manifest.url,
        sha256=manifest.sha256,
        mime=manifest.mime,
        bytes_totales=manifest.bytes_totales,
        storage_uri=manifest.storage_uri,
        fecha_descarga=manifest.fecha_descarga,
    )
