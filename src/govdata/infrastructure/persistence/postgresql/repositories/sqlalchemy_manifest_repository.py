"""Adaptador: SqlAlchemyManifestRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.manifest_repository_port import ManifestRepositoryPort
from govdata.domain.entities.manifest import Manifest
from govdata.infrastructure.persistence.postgresql.mappers import manifest_mapper
from govdata.infrastructure.persistence.postgresql.models.manifest_model import ManifestModel


class SqlAlchemyManifestRepository(ManifestRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def registrar(self, manifest: Manifest) -> Manifest:
        modelo = manifest_mapper.a_modelo(manifest)
        self._session.add(modelo)
        self._session.flush()
        return manifest_mapper.a_dominio(modelo)

    def buscar_por_hash(self, sha256: str) -> Manifest | None:
        modelo = (
            self._session.execute(select(ManifestModel).where(ManifestModel.sha256 == sha256))
            .scalars()
            .first()
        )
        return manifest_mapper.a_dominio(modelo) if modelo else None

    def listar_por_documento(self, documento_id: int) -> list[Manifest]:
        modelos = (
            self._session.execute(
                select(ManifestModel)
                .where(ManifestModel.documento_id == documento_id)
                .order_by(ManifestModel.fecha_descarga.desc())
            )
            .scalars()
            .all()
        )
        return [manifest_mapper.a_dominio(m) for m in modelos]
