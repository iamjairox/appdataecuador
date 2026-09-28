"""Caso de uso: DescubrirEntidadUseCase.

Orquesta el descubrimiento completo (publicacion + documento) para UNA
entidad, garantizando la regla de negocio mas importante del Modulo 2:
"nunca debe detener el procesamiento completo, debe continuar con la
siguiente entidad". Cualquier error de negocio esperado (timeout,
entidad sin Transparencia Activa, sin publicaciones, documento
inexistente) se captura aqui y se traduce en un resultado con
`exito=False`, nunca en una excepcion que se propague al orquestador.
"""

from __future__ import annotations

from govdata.application.dto.resultado_descubrimiento_dto import ResultadoDescubrimientoEntidadDTO
from govdata.application.use_cases.descubrir_documento_use_case import DescubrirDocumentoUseCase
from govdata.application.use_cases.descubrir_ultima_publicacion_use_case import (
    DescubrirUltimaPublicacionUseCase,
)
from govdata.config.logging_config import get_logger
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.publicacion import PublicacionMensual
from govdata.domain.exceptions.domain_exceptions import GovDataError

logger = get_logger(__name__)


class DescubrirEntidadUseCase:
    """Descubre publicacion + documento de una entidad, sin nunca propagar
    un error de negocio hacia el orquestador del pipeline."""

    def __init__(
        self,
        descubrir_publicacion: DescubrirUltimaPublicacionUseCase,
        descubrir_documento: DescubrirDocumentoUseCase,
    ) -> None:
        self._descubrir_publicacion = descubrir_publicacion
        self._descubrir_documento = descubrir_documento

    def ejecutar(self, entidad: Entidad) -> ResultadoDescubrimientoEntidadDTO:
        publicacion: PublicacionMensual | None = None
        try:
            publicacion = self._descubrir_publicacion.ejecutar(entidad)
        except GovDataError as exc:
            logger.warning(
                "descubrimiento_publicacion_fallido", entidad=entidad.nombre, error=str(exc)
            )
            return ResultadoDescubrimientoEntidadDTO(
                entidad=entidad, publicacion=None, documento=None, exito=False, error=str(exc)
            )

        try:
            documento = self._descubrir_documento.ejecutar(entidad, publicacion)
        except GovDataError as exc:
            logger.warning(
                "descubrimiento_documento_fallido", entidad=entidad.nombre, error=str(exc)
            )
            return ResultadoDescubrimientoEntidadDTO(
                entidad=entidad, publicacion=publicacion, documento=None, exito=False, error=str(exc)
            )

        return ResultadoDescubrimientoEntidadDTO(
            entidad=entidad, publicacion=publicacion, documento=documento, exito=True, error=None
        )
