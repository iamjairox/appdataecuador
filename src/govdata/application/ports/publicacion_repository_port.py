"""Puerto: PublicacionRepositoryPort."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from govdata.domain.entities.publicacion import PublicacionMensual


class PublicacionRepositoryPort(ABC):
    """Persistencia de publicaciones mensuales detectadas por entidad."""

    @abstractmethod
    def guardar_o_actualizar(self, publicacion: PublicacionMensual) -> PublicacionMensual: ...

    @abstractmethod
    def buscar_por_entidad_y_mes(
        self, entidad_id: int, mes_publicado: date
    ) -> PublicacionMensual | None:
        """Indica si ese mes ya fue procesado para esa entidad (evita reprocesar)."""

    @abstractmethod
    def buscar_ultima_por_entidad(
        self, entidad_id: int, excluir_mes: date | None = None
    ) -> PublicacionMensual | None:
        """La publicacion mas reciente (mayor `mes_publicado`) de esta
        entidad, opcionalmente excluyendo un mes especifico. Usada por el
        Motor de Monitoreo Continuo (Modulo 5, Submodulo 5.15) para ubicar
        la version 'anterior' contra la cual comparar la recien
        descubierta -- `excluir_mes` es el mes que se acaba de descubrir,
        para no compararla consigo misma."""
