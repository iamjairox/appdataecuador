"""Servicio: EnriquecimientoService -- Submodulo 6.7 (Enriquecimiento),
EL PIPELINE que conecta todo el Modulo 6:

    Persona -> Resolver identidad -> Consultar fuentes -> Actualizar
    perfil -> Generar eventos -> Guardar

La "resolucion de identidad" del pipeline (Submodulo 6.7) es la de la
PersonaMaster YA RESUELTA (Submodulo 6.1/6.2, hecha por
`ResolverOCrearPersonaMasterUseCase` antes de llegar aqui) -- este
servicio se concentra en consultar cada fuente (respetando el cache,
6.8), versionar la respuesta (6.9), y generar eventos/alertas por los
cambios detectados (6.12/6.13). Cada fuente se consulta de forma
independiente: una fuente que falla NUNCA bloquea a las demas.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime

from govdata.application.dto.resultado_enriquecimiento_dto import ResultadoEnriquecimientoDTO
from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.application.ports.fuentes_externas_ports import ExternalSourcePort
from govdata.application.ports.persona_master_repository_port import PersonaMasterRepositoryPort
from govdata.application.services.alerta_perfil_service import AlertaPerfilService
from govdata.application.services.auditoria_consulta_fuente_service import (
    AuditoriaConsultaFuenteService,
)
from govdata.application.services.cache_fuente_service import CacheFuenteService
from govdata.application.services.evento_perfil_service import EventoPerfilService
from govdata.application.services.registro_fuente_service import RegistroFuenteService
from govdata.config.logging_config import get_logger
from govdata.domain.entities.evento_perfil import EventoPerfil
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import GovDataError, PersonaMasterInvalidaError
from govdata.domain.rules.generador_alertas_perfil import generar_alertas_por_cambios
from govdata.domain.rules.generador_eventos_perfil import (
    generar_evento_fuente_actualizada,
    generar_evento_nueva_fuente,
    generar_evento_persona_enriquecida,
    generar_eventos_por_cambios,
)

logger = get_logger(__name__)


class EnriquecimientoService:
    def __init__(
        self,
        cache_service: CacheFuenteService,
        registro_fuente_service: RegistroFuenteService,
        auditoria_service: AuditoriaConsultaFuenteService,
        alerta_perfil_service: AlertaPerfilService,
        evento_perfil_service: EventoPerfilService,
        persona_master_repository: PersonaMasterRepositoryPort,
        ahora_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._cache_service = cache_service
        self._registro_fuente_service = registro_fuente_service
        self._auditoria_service = auditoria_service
        self._alerta_perfil_service = alerta_perfil_service
        self._evento_perfil_service = evento_perfil_service
        self._persona_master_repository = persona_master_repository
        self._ahora_provider = ahora_provider

    def enriquecer(
        self,
        persona_master: PersonaMaster,
        fuentes: list[ExternalSourcePort],
        senales: SenalesIdentidadDTO,
    ) -> ResultadoEnriquecimientoDTO:
        if persona_master.id is None:
            raise PersonaMasterInvalidaError("No se puede enriquecer una PersonaMaster sin id (persistirla primero)")

        inicio = time.perf_counter()
        ahora = self._ahora_provider()
        consultadas: list[str] = []
        omitidas: list[str] = []
        con_error: list[str] = []
        eventos_acumulados: list[EventoPerfil] = []
        alertas_generadas_total = 0

        for fuente_port in fuentes:
            fuente = fuente_port.fuente
            if not self._cache_service.debe_consultar(persona_master.id, fuente, ahora):
                omitidas.append(fuente.value)
                logger.info("fuente_omitida_por_cache", persona_master_id=persona_master.id, fuente=fuente.value)
                continue

            log = self._auditoria_service.iniciar(persona_master.id, fuente)
            try:
                resultado_consulta = fuente_port.consultar(senales)
            except GovDataError as exc:
                self._auditoria_service.finalizar(log, exito=False, error=str(exc))
                con_error.append(fuente.value)
                logger.warning(
                    "fuente_consulta_fallida", persona_master_id=persona_master.id, fuente=fuente.value, error=str(exc)
                )
                continue

            self._auditoria_service.finalizar(log, exito=True)
            consultadas.append(fuente.value)

            if not resultado_consulta.encontrado or not resultado_consulta.datos:
                continue

            registro, cambios = self._registro_fuente_service.registrar_respuesta(
                persona_master.id, fuente, resultado_consulta.datos, resultado_consulta.consultado_en
            )

            if registro.version == 1:
                persona_master.registrar_nueva_fuente()
                eventos_acumulados.append(generar_evento_nueva_fuente(persona_master.id, fuente, ahora))
            else:
                eventos_acumulados.append(
                    generar_evento_fuente_actualizada(persona_master.id, fuente, registro.version, ahora)
                )
            eventos_acumulados.append(generar_evento_persona_enriquecida(persona_master.id, fuente, ahora))
            eventos_acumulados.extend(generar_eventos_por_cambios(cambios, persona_master.id, ahora))

            alertas = generar_alertas_por_cambios(cambios, persona_master.id, ahora, registro.id)
            if alertas:
                self._alerta_perfil_service.guardar_lote(alertas)
                alertas_generadas_total += len(alertas)

        if eventos_acumulados:
            self._evento_perfil_service.guardar_lote(eventos_acumulados)

        if consultadas:
            persona_master.actualizado_en = ahora
            self._persona_master_repository.guardar(persona_master)

        duracion = time.perf_counter() - inicio
        logger.info(
            "enriquecimiento_completado",
            persona_master_id=persona_master.id,
            fuentes_consultadas=consultadas,
            fuentes_omitidas=omitidas,
            fuentes_con_error=con_error,
            duracion_segundos=round(duracion, 4),
        )
        return ResultadoEnriquecimientoDTO(
            persona_master_id=persona_master.id,
            fuentes_consultadas=consultadas,
            fuentes_omitidas_por_cache=omitidas,
            fuentes_con_error=con_error,
            eventos_generados=len(eventos_acumulados),
            alertas_generadas=alertas_generadas_total,
            duracion_segundos=round(duracion, 4),
        )
