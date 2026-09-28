"""Caso de uso: ListarEntidadesUseCase.

Descubre el listado completo de entidades del portal y las persiste,
sin duplicar (actualiza si ya existen, segun `EntidadRepositoryPort`).
"""

from __future__ import annotations

from govdata.application.ports.entidad_repository_port import EntidadRepositoryPort
from govdata.application.ports.portal_scraper_port import PortalScraperPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.entidad import Entidad

logger = get_logger(__name__)


class ListarEntidadesUseCase:
    """Obtiene todas las entidades del portal y las guarda/actualiza."""

    def __init__(
        self, scraper: PortalScraperPort, entidad_repository: EntidadRepositoryPort
    ) -> None:
        self._scraper = scraper
        self._entidad_repository = entidad_repository

    def ejecutar(self) -> list[Entidad]:
        dtos = self._scraper.listar_entidades()
        logger.info("entidades_descubiertas", cantidad=len(dtos))

        entidades: list[Entidad] = []
        for dto in dtos:
            entidad = Entidad(
                nombre=dto.nombre,
                url_transparencia=dto.url_transparencia,
                portal_origen=dto.portal_origen,
                activo=dto.activo,
                metadata_extra={
                    "identificador_portal": dto.identificador_portal,
                    "tipo_institucion": dto.tipo_institucion,
                },
            )
            entidades.append(self._entidad_repository.guardar_o_actualizar(entidad))

        logger.info("entidades_persistidas", cantidad=len(entidades))
        return entidades
