"""Validación individual: identificación legítima -> Foro.

La primera fase no presupone que la fuente sea accesible. Si esta falla,
persiste un intento auditable y termina sin alterar la cédula de Persona.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from govdata.application.dto.identificacion_cedula_dto import (
    EstadoMatchingCedula,
    ResultadoMatchingCedulaDTO,
)
from govdata.application.ports.consulta_cedula_port import ConsultaCedulaPort
from govdata.application.ports.foro_abogados_port import ForoAbogadosPort
from govdata.application.services.auditoria_consulta_fuente_service import (
    AuditoriaConsultaFuenteService,
)
from govdata.application.services.auditoria_orquestacion_service import AuditoriaOrquestacionService
from govdata.application.services.cola_trabajos_orquestador_service import (
    ColaTrabajosOrquestadorService,
)
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import GovDataError
from govdata.domain.rules.matching_cedula import hacer_matching_cedula
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador
from govdata.shared.security.redaccion_datos_personales import sanitizar_error_externo


class ValidarAbogadoUseCase:
    def __init__(self, consulta_cedula: ConsultaCedulaPort, foro_abogados: ForoAbogadosPort,
                 auditoria_fuente: AuditoriaConsultaFuenteService, cola: ColaTrabajosOrquestadorService,
                 auditoria: AuditoriaOrquestacionService) -> None:
        self._consulta_cedula = consulta_cedula
        self._foro_abogados = foro_abogados
        self._auditoria_fuente = auditoria_fuente
        self._cola = cola
        self._auditoria = auditoria

    async def ejecutar(self, persona_master_id: int, persona: Persona) -> tuple[str, ResultadoMatchingCedulaDTO]:
        trabajo = self._cola.encolar(
            TipoTrabajoOrquestador.VALIDACION_ABOGADO,
            {"persona_master_id": persona_master_id}, "validacion_abogado_individual", max_intentos=1,
        )
        trabajo = self._cola.iniciar_directo(trabajo)
        inicio = datetime.now(UTC)
        log = self._auditoria_fuente.iniciar(persona_master_id, FuenteExterna.CONSULTAS_ECUADOR)
        nombre = persona.nombre_completo
        partes = nombre.apellidos.split()
        paterno, materno = (partes + [""])[:2]
        try:
            candidatos = await self._consulta_cedula.consultar_por_nombres(nombre.nombres, paterno, materno)
        except GovDataError as exc:
            error_seguro = sanitizar_error_externo(exc)
            self._auditoria_fuente.finalizar(log, exito=False, error=error_seguro)
            fin = datetime.now(UTC)
            self._auditoria.registrar_fallido(str(trabajo.id), TipoPasoPipeline.IDENTIFICACION, error_seguro, inicio, fin)
            self._cola.marcar_error(trabajo, "SOURCE_UNAVAILABLE")
            return str(trabajo.id), ResultadoMatchingCedulaDTO(EstadoMatchingCedula.SOURCE_UNAVAILABLE, detalle="SOURCE_UNAVAILABLE")

        self._auditoria_fuente.finalizar(log, exito=True)
        resultado = hacer_matching_cedula(nombre.nombres, nombre.apellidos, candidatos)
        fin = datetime.now(UTC)
        self._auditoria.registrar_ejecutado(str(trabajo.id), TipoPasoPipeline.IDENTIFICACION, inicio, fin, len(candidatos))
        self._auditoria.registrar_ejecutado(str(trabajo.id), TipoPasoPipeline.MATCHING_IDENTIDAD, fin, datetime.now(UTC))
        if resultado.candidato is None:
            self._cola.marcar_completado(trabajo)
            return str(trabajo.id), resultado

        # El identificador se usa solo en este alcance y no llega a datos,
        # logs, auditoría o respuesta pública.
        cedula_transitoria = resultado.candidato.cedula
        inicio_foro = datetime.now(UTC)
        try:
            registros = await asyncio.to_thread(self._foro_abogados.buscar_por_cedula, cedula_transitoria)
        except GovDataError as exc:
            self._auditoria.registrar_fallido(
                str(trabajo.id), TipoPasoPipeline.FORO, sanitizar_error_externo(exc), inicio_foro, datetime.now(UTC)
            )
            self._cola.marcar_error(trabajo, "FORO_UNAVAILABLE")
        else:
            self._auditoria.registrar_ejecutado(
                str(trabajo.id), TipoPasoPipeline.FORO, inicio_foro, datetime.now(UTC), len(registros)
            )
            self._cola.marcar_completado(trabajo)
        finally:
            cedula_transitoria = None
        return str(trabajo.id), resultado
