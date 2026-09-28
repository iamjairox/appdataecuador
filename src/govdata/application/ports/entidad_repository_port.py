"""Puerto: EntidadRepositoryPort."""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.entidad import Entidad


class EntidadRepositoryPort(ABC):
    """Persistencia de Entidades publicas."""

    @abstractmethod
    def guardar_o_actualizar(self, entidad: Entidad) -> Entidad: ...

    @abstractmethod
    def buscar_por_id(self, entidad_id: int) -> Entidad | None: ...

    @abstractmethod
    def buscar_por_url(self, url_transparencia: str) -> Entidad | None: ...

    @abstractmethod
    def listar_activas(self, portal_origen: str | None = None) -> list[Entidad]: ...

    @abstractmethod
    def buscar_por_nombre(self, fragmento_nombre: str) -> Entidad | None:
        """Busqueda case-insensitive por coincidencia PARCIAL de nombre --
        pensada para consultas interactivas (Submodulo 4.5), donde el
        usuario escribe "Procuraduria" en vez del nombre exacto completo.
        Si hay varias coincidencias, retorna la primera (mas corta ->
        presumiblemente mas especifica)."""
