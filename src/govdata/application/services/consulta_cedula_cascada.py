"""Consulta de cédula en cascada: prueba fuentes públicas en orden.

Una fuente que responde lista vacía no corta el flujo: se intenta la
siguiente. Solo si todas fallan con error se propaga SOURCE_UNAVAILABLE.
"""

from __future__ import annotations

from collections.abc import Sequence

from govdata.application.dto.identificacion_cedula_dto import CedulaCandidateDTO
from govdata.application.ports.consulta_cedula_port import ConsultaCedulaPort
from govdata.config.logging_config import get_logger
from govdata.domain.exceptions.domain_exceptions import GovDataError
from govdata.shared.security.redaccion_datos_personales import sanitizar_error_externo

logger = get_logger(__name__)


async def consultar_cedula_en_cascada(
    fuentes: Sequence[ConsultaCedulaPort],
    nombres: str,
    apellido_paterno: str,
    apellido_materno: str,
) -> list[CedulaCandidateDTO]:
    if not fuentes:
        raise GovDataError("SOURCE_UNAVAILABLE: no hay fuentes de cédula configuradas")

    ultimo_error: GovDataError | None = None
    alguna_respuesta = False
    for fuente in fuentes:
        nombre_fuente = type(fuente).__name__
        try:
            candidatos = await fuente.consultar_por_nombres(nombres, apellido_paterno, apellido_materno)
        except GovDataError as exc:
            ultimo_error = exc
            logger.warning(
                "fuente_cedula_fallo",
                fuente=nombre_fuente,
                error=sanitizar_error_externo(exc),
            )
            continue
        alguna_respuesta = True
        if candidatos:
            logger.info("fuente_cedula_con_candidatos", fuente=nombre_fuente, candidatos=len(candidatos))
            return candidatos
        logger.info("fuente_cedula_sin_candidatos", fuente=nombre_fuente)

    if not alguna_respuesta and ultimo_error is not None:
        raise ultimo_error
    return []
