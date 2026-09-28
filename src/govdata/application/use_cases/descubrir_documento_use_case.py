"""Caso de uso: DescubrirDocumentoUseCase.

Localiza, dentro de la publicacion mensual ya detectada, el numeral
"Directorio y distributivo del personal" (via matching difuso, tolerante
a variaciones de texto) y su archivo de datos, detecta el tipo de
archivo, y persiste la metadata -- sin descargar el contenido.
"""

from __future__ import annotations

from govdata.application.ports.documento_repository_port import DocumentoRepositoryPort
from govdata.application.ports.portal_scraper_port import PortalScraperPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.documento import DocumentoTransparencia
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.publicacion import PublicacionMensual
from govdata.domain.exceptions.domain_exceptions import DocumentoNoSoportadoError
from govdata.domain.rules.detector_tipo_archivo import detectar_tipo_por_extension
from govdata.domain.rules.matcher_item_documento import seleccionar_numeral_directorio_personal
from govdata.domain.rules.seleccionador_archivo_datos import seleccionar_archivo_datos

logger = get_logger(__name__)


class DescubrirDocumentoUseCase:
    """Encuentra y persiste la metadata del documento de directorio de personal."""

    def __init__(
        self,
        scraper: PortalScraperPort,
        documento_repository: DocumentoRepositoryPort,
        umbral_confianza_item: float = 70.0,
        umbral_confianza_archivo: float = 80.0,
    ) -> None:
        self._scraper = scraper
        self._documento_repository = documento_repository
        self._umbral_confianza_item = umbral_confianza_item
        self._umbral_confianza_archivo = umbral_confianza_archivo

    def ejecutar(self, entidad: Entidad, publicacion: PublicacionMensual) -> DocumentoTransparencia:
        if publicacion.id is None:
            raise DocumentoNoSoportadoError(
                f"La publicacion de '{entidad.nombre}' no tiene id asignado (persistela primero)"
            )

        anio, mes = publicacion.mes_publicado.year, publicacion.mes_publicado.month
        numerales = self._scraper.listar_publicaciones_mes(entidad.url_transparencia, anio, mes)

        resultado_item = seleccionar_numeral_directorio_personal(
            numerales, umbral=self._umbral_confianza_item
        )
        if resultado_item is None:
            raise DocumentoNoSoportadoError(
                f"No se encontro el numeral 'Directorio y distributivo del personal' para "
                f"'{entidad.nombre}' ({anio}-{mes:02d}) entre {len(numerales)} numerales publicados"
            )

        resultado_archivo = seleccionar_archivo_datos(
            resultado_item.numeral.archivos, umbral=self._umbral_confianza_archivo
        )
        if resultado_archivo is None:
            raise DocumentoNoSoportadoError(
                f"El numeral '{resultado_item.numeral.descripcion}' de '{entidad.nombre}' "
                f"({anio}-{mes:02d}) no tiene un archivo de datos reconocible"
            )

        archivo = resultado_archivo.archivo
        tipo_archivo = detectar_tipo_por_extension(archivo.url_descarga)
        if tipo_archivo is None:
            raise DocumentoNoSoportadoError(
                f"Tipo de archivo no reconocido para '{entidad.nombre}' ({anio}-{mes:02d}): "
                f"{archivo.url_descarga}"
            )

        documento = DocumentoTransparencia(
            publicacion_id=publicacion.id,
            tipo_archivo=tipo_archivo,
            nombre_original=archivo.nombre,
            url_documento=archivo.url_descarga,
        )
        guardado = self._documento_repository.guardar_o_actualizar(documento)
        logger.info(
            "documento_descubierto",
            entidad=entidad.nombre,
            anio=anio,
            mes=mes,
            tipo_archivo=tipo_archivo.value,
            score_item=resultado_item.score,
            score_archivo=resultado_archivo.score,
        )
        return guardado
