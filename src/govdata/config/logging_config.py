"""Logging centralizado (structlog).

Todo el sistema loguea a traves de `get_logger(__name__)`. En produccion
emite JSON (consumible por n8n / ELK / OpenSearch en modulos futuros); en
desarrollo emite texto legible en consola. Cada log de negocio debe
enriquecerse con contexto vinculante (`entidad_id`, `etapa`, `intento`)
usando `logger.bind(...)`.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import structlog

from govdata.config.settings import Settings

_CONFIGURADO = False


def configurar_logging(settings: Settings) -> None:
    """Configura structlog + logging estandar. Idempotente."""
    global _CONFIGURADO
    if _CONFIGURADO:
        return

    nivel = getattr(logging, settings.logging.nivel.upper(), logging.INFO)

    ruta_archivo = Path(settings.logging.ruta_archivo)
    ruta_archivo.parent.mkdir(parents=True, exist_ok=True)

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ruta_archivo, encoding="utf-8"),
    ]

    logging.basicConfig(level=nivel, format="%(message)s", handlers=handlers, force=True)
    _silenciar_librerias_ruidosas()

    procesadores: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.logging.formato_json or settings.es_produccion():
        procesadores.append(structlog.processors.JSONRenderer())
    else:
        procesadores.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=procesadores,
        wrapper_class=structlog.make_filtering_bound_logger(nivel),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _CONFIGURADO = True


def _silenciar_librerias_ruidosas() -> None:
    """Algunas librerias de terceros (pdfminer/camelot en el Modulo 4,
    urllib3 en Modulos 2-3) loguean en DEBUG con muchisimo detalle interno
    que nunca es accionable para nosotros. Se limitan a WARNING+
    independientemente del nivel configurado para la app -- si alguien
    necesita depurar la libreria en si, puede subir su nivel a mano.
    """
    for nombre in ("pdfminer", "camelot", "PIL", "urllib3"):
        logging.getLogger(nombre).setLevel(logging.WARNING)


def get_logger(nombre: str) -> structlog.stdlib.BoundLogger:
    """Retorna un logger estructurado. Configura logging con defaults si
    aun no se ha llamado `configurar_logging` explicitamente (ej. en tests).
    """
    if not _CONFIGURADO:
        from govdata.config.settings import get_settings

        configurar_logging(get_settings())
    return structlog.get_logger(nombre)
