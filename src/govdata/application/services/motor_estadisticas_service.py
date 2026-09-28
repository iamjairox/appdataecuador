"""Servicio: MotorEstadisticasService -- Submodulo 9.12.

Calcula las estadisticas AGREGADAS (todas las corridas conocidas, insumo
del Dashboard interno 9.11) a partir de la Auditoria por Etapa (9.10/9.15)
-- nunca recalcula nada que Modulos 5/7/8 ya calcularon, solo agrega lo
que `AuditoriaOrquestacionService` ya registro por cada paso."""

from __future__ import annotations

from govdata.application.dto.estadisticas_orquestacion_dto import EstadisticasOrquestacionDTO
from govdata.application.ports.auditoria_etapa_repository_port import AuditoriaEtapaRepositoryPort
from govdata.domain.value_objects.estado_paso import EstadoPaso
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline


class MotorEstadisticasService:
    def __init__(self, repository: AuditoriaEtapaRepositoryPort) -> None:
        self._repository = repository

    def calcular(self) -> EstadisticasOrquestacionDTO:
        etapas = self._repository.listar_todo()

        def _cantidad(tipo: TipoPasoPipeline) -> int:
            return sum(e.cantidad_registros for e in etapas if e.tipo_paso == tipo and e.estado_paso == EstadoPaso.EJECUTADO)

        def _consultas(tipo: TipoPasoPipeline) -> int:
            return len([e for e in etapas if e.tipo_paso == tipo and e.estado_paso == EstadoPaso.EJECUTADO])

        # `EnriquecimientoAcademicoService`/`EnriquecimientoForoService`
        # (Modulos 7/8, REUTILIZADOS) deciden el cache INTERNAMENTE --
        # cuando `debe_consultar()` da False, `GovDataPipelineOrchestrator`
        # registra el paso como OMITIDO con razon "cache_vigente" (nunca
        # llego a consultar la fuente); cuando da True, lo registra como
        # EJECUTADO (consulto de verdad). Cache hit/miss se leen
        # directamente de esa decision, ya tomada -- nunca se reevalua.
        senescyt_foro = [e for e in etapas if e.tipo_paso in (TipoPasoPipeline.SENESCYT, TipoPasoPipeline.FORO)]
        cache_hit = len([e for e in senescyt_foro if e.estado_paso == EstadoPaso.OMITIDO and e.razon_omision == "cache_vigente"])
        cache_miss = len([e for e in senescyt_foro if e.estado_paso == EstadoPaso.EJECUTADO])

        return EstadisticasOrquestacionDTO(
            funcionarios_encontrados=_cantidad(TipoPasoPipeline.EXTRACCION),
            funcionarios_juridicos=_cantidad(TipoPasoPipeline.PERFIL),
            consultas_senescyt=_consultas(TipoPasoPipeline.SENESCYT),
            consultas_foro=_consultas(TipoPasoPipeline.FORO),
            cambios_detectados=_cantidad(TipoPasoPipeline.COMPARACION),
            alertas=_cantidad(TipoPasoPipeline.ALERTAS),
            errores=len([e for e in etapas if e.estado_paso == EstadoPaso.FALLIDO]),
            cache_hit=cache_hit,
            cache_miss=cache_miss,
        )
