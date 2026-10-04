"""Ejecuta el monitoreo masivo de DPE una vez al día a las 03:00 Ecuador."""

from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from govdata.config.container import Container
from govdata.infrastructure.api.routes.companias import actualizar_directorio

ZONA_ECUADOR = ZoneInfo("America/Guayaquil")
HORA_EJECUCION = 3
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("programador_dpe")


def siguiente_ejecucion(ahora: datetime) -> datetime:
    objetivo = ahora.replace(hour=HORA_EJECUCION, minute=0, second=0, microsecond=0)
    return objetivo if ahora < objetivo else objetivo + timedelta(days=1)


def ejecutar_monitoreo() -> None:
    logger.info("Inicia verificación automática diaria de DPE")
    container = Container()
    with container.nueva_sesion() as sesion:
        servicio = container.crear_monitoreo_service(sesion)
        try:
            resultados = servicio.monitorear_masiva()
            actualizados = sum(1 for resultado in resultados if resultado.hubo_cambio)
            logger.info("Finaliza DPE: entidades=%s actualizadas=%s sin_novedad=%s", len(resultados), actualizados, len(resultados) - actualizados)
        finally:
            servicio.cerrar()


def actualizar_directorio_supercias() -> None:
    """Actualiza Supercias únicamente si su fecha oficial cambió."""
    logger.info("Inicia verificación automática del directorio de Supercias")
    container = Container()
    with container.nueva_sesion() as sesion:
        resultado = actualizar_directorio(forzar=False, sesion=sesion)
    if resultado["actualizado"]:
        logger.info(
            "Supercias actualizada: empresas=%s versión=%s",
            resultado["total_importadas"],
            resultado["periodo_fuente"],
        )
    else:
        logger.info("Supercias sin novedades: versión=%s", resultado["periodo_fuente"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--once",
        action="store_true",
        help="ejecuta una única revisión; útil para el Programador de tareas de Windows",
    )
    args = parser.parse_args()
    if args.once:
        try:
            actualizar_directorio_supercias()
        except Exception:
            logger.exception("Falló la verificación automática de Supercias")
        ejecutar_monitoreo()
        return

    while True:
        ahora = datetime.now(ZONA_ECUADOR)
        proxima = siguiente_ejecucion(ahora)
        logger.info("Próxima verificación automática DPE: %s", proxima.isoformat())
        time.sleep(max(1, (proxima - ahora).total_seconds()))
        try:
            actualizar_directorio_supercias()
        except Exception:
            logger.exception("Falló la verificación automática de Supercias")
        try:
            ejecutar_monitoreo()
        except Exception:
            logger.exception("Falló la verificación automática DPE; se reintentará al día siguiente")


if __name__ == "__main__":
    main()
