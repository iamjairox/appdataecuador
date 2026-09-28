"""Servicio: CacheService -- Submodulo 4.9 (Cache inteligente).

Decide si una entidad necesita volver a pasar por el pipeline completo
(descubrir -> descargar -> extraer) o si ya hay resultados vigentes en
base de datos. Dos preguntas distintas, deliberadamente separadas:

  - `evaluar_entidad`: "¿ya proceso esta entidad recientemente?" -- una
    decision de TIEMPO (`dias_vigencia`, Motor de Reglas). Si vence,
    ConsultaService igual vuelve a correr descubrir/descargar -- pero eso
    NO implica reprocesar la extraccion si el archivo no cambio.
  - `requiere_reextraccion`: "¿el documento (posiblemente redescargado)
    tiene una version para la que YA existen funcionarios extraidos?" --
    una decision de CONTENIDO (hash/version, Modulo 3), no de tiempo. Se
    apoya en que `Documento.version` solo se incrementa cuando cambia el
    hash real del archivo (ver Modulo 3).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime

from govdata.application.dto.decision_cache_dto import DecisionCacheDTO
from govdata.application.ports.documento_repository_port import DocumentoRepositoryPort
from govdata.application.ports.funcionario_repository_port import FuncionarioRepositoryPort
from govdata.application.ports.publicacion_repository_port import PublicacionRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.documento import EstadoDocumento
from govdata.domain.rules.reglas_configurables import ReglasCache

logger = get_logger(__name__)


class CacheService:
    def __init__(
        self,
        publicacion_repository: PublicacionRepositoryPort,
        documento_repository: DocumentoRepositoryPort,
        funcionario_repository: FuncionarioRepositoryPort,
        reglas: ReglasCache,
        ahora_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._publicacion_repository = publicacion_repository
        self._documento_repository = documento_repository
        self._funcionario_repository = funcionario_repository
        self._reglas = reglas
        self._ahora_provider = ahora_provider

    def evaluar_entidad(self, entidad_id: int, mes_publicado: date) -> DecisionCacheDTO:
        publicacion = self._publicacion_repository.buscar_por_entidad_y_mes(entidad_id, mes_publicado)
        if publicacion is None or publicacion.id is None:
            return DecisionCacheDTO(vigente=False, motivo="sin_publicacion_previa")

        documento = self._documento_repository.buscar_por_publicacion(publicacion.id)
        if documento is None:
            return DecisionCacheDTO(vigente=False, motivo="sin_documento_previo")

        if documento.estado != EstadoDocumento.DESCARGADO:
            return DecisionCacheDTO(
                vigente=False, motivo=f"documento_en_estado_{documento.estado.value}", documento=documento
            )

        if documento.descargado_en is None:
            return DecisionCacheDTO(vigente=False, motivo="sin_fecha_descarga", documento=documento)

        if not self._tiene_extraccion_vigente(documento.id):  # type: ignore[arg-type]
            return DecisionCacheDTO(vigente=False, motivo="sin_extraccion_previa", documento=documento)

        dias_transcurridos = (self._ahora_provider() - documento.descargado_en).days
        if dias_transcurridos >= self._reglas.dias_vigencia:
            return DecisionCacheDTO(vigente=False, motivo="vigencia_expirada", documento=documento)

        logger.info("cache_vigente", entidad_id=entidad_id, documento_id=documento.id)
        return DecisionCacheDTO(vigente=True, motivo="cache_vigente", documento=documento)

    def requiere_reextraccion(self, documento_id: int) -> bool:
        """True si el documento (version actual) NO tiene funcionarios
        extraidos todavia -- ej. porque acaba de redescargarse y trajo un
        hash distinto (Modulo 3 incremento `version`)."""
        return not self._tiene_extraccion_vigente(documento_id)

    def _tiene_extraccion_vigente(self, documento_id: int) -> bool:
        return len(self._funcionario_repository.listar_por_documento(documento_id)) > 0
