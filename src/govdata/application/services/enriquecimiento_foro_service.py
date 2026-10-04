"""Servicio: EnriquecimientoForoService -- el tramo "Foro de Abogados"
del pipeline obligatorio del Modulo 8:

    ... -> SENESCYT -> Obtener Cedula -> Foro de Abogados -> Extraer
    informacion profesional -> Fusionar -> Guardar historial -> Mostrar
    resultado

Este servicio arranca en "Foro de Abogados" (la cedula ya la trae la
`Persona` -- Modulo 1, campo `cedula` ya existente -- por eso el caso de
uso que orquesta el flujo completo, `ConsultarEntidadUseCase`, pasa la
`Persona` completa aqui, no solo su `PersonaMaster`) y ejecuta:
Extraer -> Normalizar -> Comparar -> Guardar version -> Alertas ->
Eventos -> Resultado. Respeta el cache por persona (8.8): si la ultima
consulta exitosa sigue vigente, no llama al Foro.

Los campos de auditoria HTTP-especificos (`codigo_http`,
`captcha_detectado`, `pagina_vacia`, Submodulo 8.17) son responsabilidad
del adaptador (Submodulo 8.2) -- `ForoAbogadosPort` es un contrato puro
de datos de dominio (`list[RegistroForoDTO]`), nunca expone detalles
HTTP; este servicio los deja en su valor por defecto, la auditoria fina
de la respuesta vive en los logs del adaptador."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime

from govdata.application.dto.diferencia_registro_foro_dto import DiferenciaRegistroForoDTO
from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.dto.resultado_enriquecimiento_foro_dto import (
    ResultadoEnriquecimientoForoDTO,
)
from govdata.application.ports.foro_abogados_port import ForoAbogadosPort
from govdata.application.ports.persona_repository_port import PersonaRepositoryPort
from govdata.application.services.alerta_foro_service import AlertaForoService
from govdata.application.services.cache_foro_service import CacheForoService
from govdata.application.services.comparacion_foro_service import ComparacionForoService
from govdata.application.services.consulta_foro_service import ConsultaForoService
from govdata.application.services.evento_foro_service import EventoForoService
from govdata.application.services.registro_foro_service import RegistroForoService
from govdata.config.logging_config import get_logger
from govdata.domain.entities.alerta_foro import AlertaForo
from govdata.domain.entities.evento_foro import EventoForo
from govdata.domain.entities.persona import Persona
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import GovDataError, PersonaMasterInvalidaError
from govdata.domain.rules.generador_alertas_foro import generar_alertas_por_diferencia
from govdata.domain.rules.generador_eventos_foro import (
    generar_evento_consulta_exitosa,
    generar_evento_consulta_fallida,
    generar_eventos_por_diferencia,
)
from govdata.domain.rules.normalizador_foro import normalizar_registro_foro
from govdata.domain.rules.reglas_foro import RuleEngineForo
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo

logger = get_logger(__name__)


def _serializar_respuesta(diferencias: list[DiferenciaRegistroForoDTO]) -> dict:
    def _dto_a_dict(dto: object) -> dict:
        return asdict(dto)  # type: ignore[call-overload]

    return {"registros_actuales": [_dto_a_dict(d.datos_actuales) for d in diferencias if d.datos_actuales is not None]}


class EnriquecimientoForoService:
    def __init__(
        self,
        cache_service: CacheForoService,
        foro_port: ForoAbogadosPort,
        consulta_service: ConsultaForoService,
        comparacion_service: ComparacionForoService,
        registro_service: RegistroForoService,
        alerta_service: AlertaForoService,
        evento_service: EventoForoService,
        rule_engine_foro: RuleEngineForo,
        persona_repository: PersonaRepositoryPort | None = None,
        ahora_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._cache_service = cache_service
        self._foro_port = foro_port
        self._consulta_service = consulta_service
        self._comparacion_service = comparacion_service
        self._registro_service = registro_service
        self._alerta_service = alerta_service
        self._evento_service = evento_service
        self._rule_engine_foro = rule_engine_foro
        self._persona_repository = persona_repository
        self._ahora_provider = ahora_provider

    def enriquecer(
        self, persona_master: PersonaMaster, persona: Persona, job_id: str | None = None
    ) -> ResultadoEnriquecimientoForoDTO:
        if persona_master.id is None:
            raise PersonaMasterInvalidaError("No se puede consultar el Foro para una PersonaMaster sin id (persistirla primero)")

        inicio = time.perf_counter()
        ahora = self._ahora_provider()

        if not self._cache_service.debe_consultar(persona_master.id, ahora):
            logger.info("consulta_foro_omitida_por_cache", persona_master_id=persona_master.id)
            return ResultadoEnriquecimientoForoDTO(
                persona_master_id=persona_master.id, consultado=False, duracion_segundos=time.perf_counter() - inicio,
            )

        consulta = self._consulta_service.iniciar(persona_master.id, job_id=job_id)
        try:
            resultados_crudos = self._foro_port.buscar_por_persona(persona)
        except GovDataError as exc:
            self._consulta_service.finalizar(consulta, exito=False, error=str(exc))
            self._evento_service.guardar_lote([generar_evento_consulta_fallida(persona_master.id, ahora, str(exc))])
            logger.warning("consulta_foro_fallida", persona_master_id=persona_master.id, error=str(exc))
            return ResultadoEnriquecimientoForoDTO(
                persona_master_id=persona_master.id, consultado=True, error=str(exc),
                duracion_segundos=time.perf_counter() - inicio,
            )

        actuales = [normalizar_registro_foro(dto, self._rule_engine_foro) for dto in resultados_crudos]
        self._persistir_cedula_verificada(persona, actuales)
        diferencias = self._comparacion_service.comparar(persona_master.id, actuales)
        cambios_reales = [d for d in diferencias if d.es_cambio]

        fecha = ahora.date()
        eventos_acumulados: list[EventoForo] = []
        alertas_acumuladas: list[AlertaForo] = []

        for diferencia in diferencias:
            registro_actualizado = self._registro_service.aplicar_diferencia(
                diferencia, persona_master.id, consulta.id, fecha, ahora
            )
            if not diferencia.es_cambio:
                continue
            registro_id = registro_actualizado.id if registro_actualizado is not None else None
            eventos_acumulados.extend(generar_eventos_por_diferencia(diferencia, persona_master.id, ahora))
            alertas_acumuladas.extend(generar_alertas_por_diferencia(diferencia, persona_master.id, ahora, registro_id))

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
            "enriquecimiento_foro_completado", persona_master_id=persona_master.id,
            cambios_detectados=len(cambios_reales), duracion_segundos=round(duracion, 4),
        )
        return ResultadoEnriquecimientoForoDTO(
            persona_master_id=persona_master.id,
            consultado=True,
            registros_nuevos=len([d for d in cambios_reales if d.tipo_cambio == TipoCambioForo.DATO_NUEVO]),
            registros_eliminados=len([d for d in cambios_reales if d.tipo_cambio == TipoCambioForo.DATO_ELIMINADO]),
            cambios_detectados=len(cambios_reales),
            alertas_generadas=len(alertas_acumuladas),
            eventos_generados=len(eventos_acumulados),
            duracion_segundos=round(duracion, 4),
            tipos_cambio=[d.tipo_cambio.value for d in cambios_reales],
        )

    def _persistir_cedula_verificada(self, persona: Persona, registros: list[RegistroForoDTO]) -> None:
        """Guarda una cédula que el Foro confirmó para esta persona.

        El adaptador solo emite registros después de una identificación
        inequívoca; aun así, este límite protege la identidad ya persistida:
        nunca reemplaza una cédula existente ni viola su unicidad.
        """
        if self._persona_repository is None or persona.id is None or persona.cedula:
            return

        cedulas = {registro.cedula.strip() for registro in registros if registro.cedula and registro.cedula.strip().isdigit()}
        if len(cedulas) != 1:
            return

        cedula = cedulas.pop()
        titular_existente = self._persona_repository.buscar_por_cedula(cedula)
        if titular_existente is not None and titular_existente.id != persona.id:
            logger.warning(
                "cedula_foro_no_asignada_por_conflicto",
                persona_id=persona.id,
                persona_existente_id=titular_existente.id,
            )
            return

        persona.cedula = cedula
        self._persona_repository.guardar(persona)
        logger.info("cedula_foro_persistida", persona_id=persona.id)
