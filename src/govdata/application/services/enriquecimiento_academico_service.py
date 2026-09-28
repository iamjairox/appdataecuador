"""Servicio: EnriquecimientoAcademicoService -- EL PIPELINE del Modulo 7:

    Persona -> Resolver Persona Master -> Consultar SENESCYT -> Normalizar
    -> Comparar contra version anterior -> Guardar nueva version ->
    Actualizar Perfil Maestro -> Alertas -> Eventos -> Resultado enriquecido

"Resolver Persona Master" ya sucedio ANTES de llegar aqui (Modulo 6,
`ResolverOCrearPersonaMasterUseCase`, REUTILIZADO sin modificar) -- este
servicio arranca en "Consultar SENESCYT" y ejecuta el resto de la
tuberia. Respeta el cache por persona (7.10): si la ultima consulta
exitosa sigue vigente, no llama a SENESCYT.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime

from govdata.application.dto.diferencia_titulo_dto import DiferenciaTituloDTO
from govdata.application.dto.resultado_enriquecimiento_academico_dto import (
    ResultadoEnriquecimientoAcademicoDTO,
)
from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.application.ports.senescyt_port import SenescytPort
from govdata.application.services.alerta_academica_service import AlertaAcademicaService
from govdata.application.services.cache_senescyt_service import CacheSenescytService
from govdata.application.services.comparacion_academica_service import ComparacionAcademicaService
from govdata.application.services.consulta_senescyt_service import ConsultaSenescytService
from govdata.application.services.evento_academico_service import EventoAcademicoService
from govdata.application.services.titulo_academico_service import TituloAcademicoService
from govdata.config.logging_config import get_logger
from govdata.domain.entities.alerta_academica import AlertaAcademica
from govdata.domain.entities.evento_academico import EventoAcademico
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import GovDataError, PersonaMasterInvalidaError
from govdata.domain.rules.generador_alertas_academicas import generar_alertas_por_diferencia
from govdata.domain.rules.generador_eventos_academicos import (
    generar_evento_consulta_exitosa,
    generar_evento_consulta_fallida,
    generar_eventos_por_diferencia,
)
from govdata.domain.rules.normalizador_academico import normalizar_persona_academica
from govdata.domain.rules.reglas_academicas import RuleEngineAcademico
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico

logger = get_logger(__name__)


def _serializar_respuesta(diferencias: list[DiferenciaTituloDTO]) -> dict:
    def _dto_a_dict(dto: object) -> dict:
        campos = asdict(dto)  # type: ignore[call-overload]
        return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in campos.items()}

    return {
        "titulos_actuales": [
            _dto_a_dict(d.datos_actuales) for d in diferencias if d.datos_actuales is not None
        ]
    }


class EnriquecimientoAcademicoService:
    def __init__(
        self,
        cache_service: CacheSenescytService,
        senescyt_port: SenescytPort,
        consulta_service: ConsultaSenescytService,
        comparacion_service: ComparacionAcademicaService,
        titulo_service: TituloAcademicoService,
        alerta_service: AlertaAcademicaService,
        evento_service: EventoAcademicoService,
        rule_engine_academico: RuleEngineAcademico,
        ahora_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._cache_service = cache_service
        self._senescyt_port = senescyt_port
        self._consulta_service = consulta_service
        self._comparacion_service = comparacion_service
        self._titulo_service = titulo_service
        self._alerta_service = alerta_service
        self._evento_service = evento_service
        self._rule_engine_academico = rule_engine_academico
        self._ahora_provider = ahora_provider

    def enriquecer(self, persona_master: PersonaMaster, senales: SenalesIdentidadDTO) -> ResultadoEnriquecimientoAcademicoDTO:
        if persona_master.id is None:
            raise PersonaMasterInvalidaError("No se puede enriquecer una PersonaMaster sin id (persistirla primero)")

        inicio = time.perf_counter()
        ahora = self._ahora_provider()

        if not self._cache_service.debe_consultar(persona_master.id, ahora):
            logger.info("consulta_senescyt_omitida_por_cache", persona_master_id=persona_master.id)
            return ResultadoEnriquecimientoAcademicoDTO(
                persona_master_id=persona_master.id, consultado=False, duracion_segundos=time.perf_counter() - inicio,
            )

        consulta = self._consulta_service.iniciar(persona_master.id)
        try:
            resultados_crudos = self._senescyt_port.consultar_por_persona_master(persona_master)
        except GovDataError as exc:
            self._consulta_service.finalizar(consulta, exito=False, error=str(exc))
            self._evento_service.guardar_lote(
                [generar_evento_consulta_fallida(persona_master.id, ahora, str(exc))]
            )
            logger.warning("consulta_senescyt_fallida", persona_master_id=persona_master.id, error=str(exc))
            return ResultadoEnriquecimientoAcademicoDTO(
                persona_master_id=persona_master.id, consultado=True, error=str(exc),
                duracion_segundos=time.perf_counter() - inicio,
            )

        actuales = [normalizar_persona_academica(dto, self._rule_engine_academico) for dto in resultados_crudos]
        diferencias = self._comparacion_service.comparar(persona_master.id, actuales)
        cambios_reales = [d for d in diferencias if d.es_cambio]

        fecha = ahora.date()
        eventos_acumulados: list[EventoAcademico] = []
        alertas_acumuladas: list[AlertaAcademica] = []

        for diferencia in diferencias:
            titulo_actualizado = self._titulo_service.aplicar_diferencia(
                diferencia, persona_master.id, consulta.id, fecha, ahora
            )
            if not diferencia.es_cambio:
                continue
            titulo_id = titulo_actualizado.id if titulo_actualizado is not None else None
            eventos_acumulados.extend(generar_eventos_por_diferencia(diferencia, persona_master.id, ahora))
            alertas_acumuladas.extend(
                generar_alertas_por_diferencia(diferencia, persona_master.id, ahora, titulo_id)
            )

        eventos_acumulados.append(generar_evento_consulta_exitosa(persona_master.id, ahora, len(actuales)))

        if alertas_acumuladas:
            self._alerta_service.guardar_lote(alertas_acumuladas)
        if eventos_acumulados:
            self._evento_service.guardar_lote(eventos_acumulados)

        self._consulta_service.finalizar(
            consulta, exito=True, version_resultante=len(actuales), respuesta_cruda=_serializar_respuesta(diferencias),
        )

        duracion = time.perf_counter() - inicio
        logger.info(
            "enriquecimiento_academico_completado", persona_master_id=persona_master.id,
            cambios_detectados=len(cambios_reales), duracion_segundos=round(duracion, 4),
        )
        return ResultadoEnriquecimientoAcademicoDTO(
            persona_master_id=persona_master.id,
            consultado=True,
            titulos_nuevos=len([d for d in cambios_reales if d.tipo_cambio == TipoCambioAcademico.TITULO_NUEVO]),
            titulos_eliminados=len([d for d in cambios_reales if d.tipo_cambio == TipoCambioAcademico.TITULO_ELIMINADO]),
            cambios_detectados=len(cambios_reales),
            alertas_generadas=len(alertas_acumuladas),
            eventos_generados=len(eventos_acumulados),
            duracion_segundos=round(duracion, 4),
            tipos_cambio=[d.tipo_cambio.value for d in cambios_reales],
        )
