"""Servicio: TimelineService -- Submodulo 5.13.

Construye la linea de tiempo de una entidad a partir de su historial de
`Verificacion` (Submodulos 5.10/5.15 -- "mantener un historial de
verificaciones incluso cuando no haya cambios"), enriquecida con la
cantidad de alertas y cambios detectados en cada punto (via `Alerta` y
`AuditoriaComparacion`, ambas indexadas por `documento_id`). Solo LEE --
no genera ni persiste nada nuevo."""

from __future__ import annotations

from govdata.application.dto.resultado_unificado_dto import EntidadResumenDTO
from govdata.application.dto.timeline_dto import PuntoTimelineDTO, TimelineEntidadDTO
from govdata.application.ports.alerta_repository_port import AlertaRepositoryPort
from govdata.application.ports.auditoria_comparacion_repository_port import (
    AuditoriaComparacionRepositoryPort,
)
from govdata.application.ports.documento_repository_port import DocumentoRepositoryPort
from govdata.application.ports.verificacion_repository_port import VerificacionRepositoryPort
from govdata.domain.entities.verificacion import Verificacion


class TimelineService:
    def __init__(
        self,
        verificacion_repository: VerificacionRepositoryPort,
        alerta_repository: AlertaRepositoryPort,
        auditoria_repository: AuditoriaComparacionRepositoryPort,
        documento_repository: DocumentoRepositoryPort,
    ) -> None:
        self._verificacion_repository = verificacion_repository
        self._alerta_repository = alerta_repository
        self._auditoria_repository = auditoria_repository
        self._documento_repository = documento_repository

    def construir(self, entidad: EntidadResumenDTO) -> TimelineEntidadDTO:
        verificaciones = self._verificacion_repository.listar_por_entidad(entidad.id)
        puntos = [self._punto_desde_verificacion(v) for v in verificaciones]
        return TimelineEntidadDTO(entidad=entidad, puntos=puntos)

    def _punto_desde_verificacion(self, verificacion: Verificacion) -> PuntoTimelineDTO:
        cantidad_alertas = 0
        cantidad_cambios = 0
        version_documento = None
        mes_publicado = None

        if verificacion.documento_id is not None:
            cantidad_alertas = len(self._alerta_repository.listar_por_documento(verificacion.documento_id))
            cantidad_cambios = sum(
                auditoria.cambios_detectados
                for auditoria in self._auditoria_repository.listar_por_documento(verificacion.documento_id)
            )
            documento = self._documento_repository.buscar_por_id(verificacion.documento_id)
            if documento is not None:
                version_documento = documento.version

        return PuntoTimelineDTO(
            verificado_en=verificacion.verificado_en,
            documento_id=verificacion.documento_id,
            version_documento=version_documento,
            hubo_cambio=verificacion.hubo_cambio,
            cantidad_cambios=cantidad_cambios,
            cantidad_alertas=cantidad_alertas,
            mes_publicado=mes_publicado,
        )
