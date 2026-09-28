"""Puerto: ManifestRepositoryPort."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.manifest import Manifest


class ManifestRepositoryPort(ABC):
    """Persistencia del registro canonico (append-only) de cada version
    de archivo efectivamente almacenada."""

    @abstractmethod
    def registrar(self, manifest: Manifest) -> Manifest: ...

    @abstractmethod
    def buscar_por_hash(self, sha256: str) -> Manifest | None:
        """Deduplicacion GLOBAL: si ya existe un Manifest con este hash
        (de cualquier documento/entidad), el contenido ya esta en storage
        -- no hace falta volver a subirlo, solo registrar un Manifest
        nuevo apuntando al mismo `storage_uri`.
        """

    @abstractmethod
    def listar_por_documento(self, documento_id: int) -> list[Manifest]:
        """Historial de versiones almacenadas de un documento."""
