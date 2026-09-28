"""Caso de uso: DescubrirUltimaPublicacionUseCase.

Determina dinamicamente el mes mas reciente publicado de Transparencia
Activa para una entidad. No asume el anio actual tiene publicaciones:
si viene vacio, retrocede anio por anio (hasta `anios_lookback_maximo`)
antes de rendirse.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime

from govdata.application.ports.portal_scraper_port import PortalScraperPort
from govdata.application.ports.publicacion_repository_port import PublicacionRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.publicacion import PublicacionMensual
from govdata.domain.exceptions.domain_exceptions import PublicacionNoDisponibleError
from govdata.domain.rules.detector_ultimo_mes import seleccionar_mes_mas_reciente

logger = get_logger(__name__)


class DescubrirUltimaPublicacionUseCase:
    """Encuentra y persiste la ultima publicacion mensual de una entidad."""

    def __init__(
        self,
        scraper: PortalScraperPort,
        publicacion_repository: PublicacionRepositoryPort,
        anios_lookback_maximo: int = 3,
        anio_actual_provider: Callable[[], int] = lambda: datetime.now(UTC).year,
    ) -> None:
        self._scraper = scraper
        self._publicacion_repository = publicacion_repository
        self._anios_lookback_maximo = anios_lookback_maximo
        self._anio_actual_provider = anio_actual_provider

    def ejecutar(self, entidad: Entidad) -> PublicacionMensual:
        if entidad.id is None:
            raise PublicacionNoDisponibleError(
                f"La entidad '{entidad.nombre}' no tiene id asignado (persistala primero)"
            )

        anio_actual = self._anio_actual_provider()
        for offset in range(self._anios_lookback_maximo + 1):
            anio = anio_actual - offset
            meses_publicados = self._scraper.listar_meses_publicados(entidad.url_transparencia, anio)
            mes = seleccionar_mes_mas_reciente(meses_publicados)
            if mes is not None:
                publicacion = PublicacionMensual(
                    entidad_id=entidad.id,
                    mes_publicado=date(anio, mes, 1),
                    url_item=f"{entidad.url_transparencia}?anio={anio}&mes={mes}",
                )
                guardada = self._publicacion_repository.guardar_o_actualizar(publicacion)
                logger.info(
                    "ultima_publicacion_detectada",
                    entidad_id=entidad.id,
                    entidad=entidad.nombre,
                    anio=anio,
                    mes=mes,
                )
                return guardada

        raise PublicacionNoDisponibleError(
            f"'{entidad.nombre}' no tiene publicaciones de Transparencia Activa en los "
            f"ultimos {self._anios_lookback_maximo + 1} anios ({anio_actual - self._anios_lookback_maximo}-{anio_actual})"
        )
