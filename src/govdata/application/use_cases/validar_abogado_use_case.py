"""Validación individual: identificación legítima -> Foro.

La primera fase no presupone que la fuente sea accesible. Si esta falla,
persiste un intento auditable y termina sin alterar la cédula de Persona.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from govdata.application.dto.identificacion_cedula_dto import (
    ResultadoMatchingCedulaDTO,
)
from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.ports.consulta_cedula_port import ConsultaCedulaPort
from govdata.application.ports.foro_abogados_port import ForoAbogadosPort
from govdata.application.services.auditoria_consulta_fuente_service import (
    AuditoriaConsultaFuenteService,
)
from govdata.application.services.auditoria_orquestacion_service import AuditoriaOrquestacionService
from govdata.application.services.cola_trabajos_orquestador_service import (
    ColaTrabajosOrquestadorService,
)
from govdata.application.services.consulta_cedula_cascada import consultar_cedula_en_cascada
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import GovDataError
from govdata.domain.rules.matching_cedula import hacer_matching_cedula
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador
from govdata.shared.security.redaccion_datos_personales import sanitizar_error_externo


@dataclass(frozen=True, slots=True)
class ResultadoValidacionAbogado:
    """Resultado completo de la validación de abogado."""

    job_id: str
    estado: str
    # Información del funcionario (desde Transparencia)
    institucion: str
    cargo: str
    dependencia: str
    correo_institucional: str | None
    telefono_institucional: str | None
    ciudad: str | None
    # Resultado del matching de identidad
    estado_identificacion: str
    confianza: float
    cedula: str | None = None
    # Información del Foro de Abogados
    registro_foro: str | None = None
    estado_foro: str | None = None
    provincia_foro: str | None = None
    correo_personal: str | None = None
    celular_personal: str | None = None
    # Metadatos
    fuente: str | None = None
    fecha_consulta: datetime | None = None
    detalle: str | None = None


class ValidarAbogadoUseCase:
    def __init__(self, consulta_cedula: ConsultaCedulaPort, foro_abogados: ForoAbogadosPort,
                 auditoria_fuente: AuditoriaConsultaFuenteService, cola: ColaTrabajosOrquestadorService,
                 auditoria: AuditoriaOrquestacionService, persona_repository: Any,
                 consulta_cedula_fallback: ConsultaCedulaPort | None = None,
                 consulta_cedula_fallback2: ConsultaCedulaPort | None = None,
                 consulta_cedula_fallback3: ConsultaCedulaPort | None = None) -> None:
        self._consulta_cedula = consulta_cedula
        self._consulta_cedula_fallback = consulta_cedula_fallback
        self._consulta_cedula_fallback2 = consulta_cedula_fallback2
        self._consulta_cedula_fallback3 = consulta_cedula_fallback3
        self._foro_abogados = foro_abogados
        self._auditoria_fuente = auditoria_fuente
        self._cola = cola
        self._auditoria = auditoria
        self._persona_repository = persona_repository

    async def ejecutar(self, persona_master_id: int, persona: Persona) -> ResultadoValidacionAbogado:
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
        
        # Información base del funcionario (desde Transparencia)
        info_funcionario = self._construir_info_funcionario(persona)
        
        try:
            fuentes = [self._consulta_cedula]
            if self._consulta_cedula_fallback is not None:
                fuentes.append(self._consulta_cedula_fallback)
            if self._consulta_cedula_fallback2 is not None:
                fuentes.append(self._consulta_cedula_fallback2)
            if self._consulta_cedula_fallback3 is not None:
                fuentes.append(self._consulta_cedula_fallback3)
            candidatos = await consultar_cedula_en_cascada(fuentes, nombre.nombres, paterno, materno)
        except GovDataError as exc:
            error_seguro = sanitizar_error_externo(exc)
            self._auditoria_fuente.finalizar(log, exito=False, error=error_seguro)
            fin = datetime.now(UTC)
            self._auditoria.registrar_fallido(str(trabajo.id), TipoPasoPipeline.IDENTIFICACION, error_seguro, inicio, fin)
            self._cola.marcar_error(trabajo, "SOURCE_UNAVAILABLE")
            return self._construir_resultado_error(trabajo, info_funcionario, "SOURCE_UNAVAILABLE", error_seguro)

        self._auditoria_fuente.finalizar(log, exito=True)
        resultado = hacer_matching_cedula(nombre.nombres, nombre.apellidos, candidatos)
        fin = datetime.now(UTC)
        self._auditoria.registrar_ejecutado(str(trabajo.id), TipoPasoPipeline.IDENTIFICACION, inicio, fin, len(candidatos))
        self._auditoria.registrar_ejecutado(str(trabajo.id), TipoPasoPipeline.MATCHING_IDENTIDAD, fin, datetime.now(UTC))
        
        if resultado.candidato is None:
            self._cola.marcar_completado(trabajo)
            return self._construir_resultado_sin_identificacion(trabajo, info_funcionario, resultado)

        # Guardar la cédula en la base de datos para que aparezca en todas las consultas
        cedula_transitoria = resultado.candidato.cedula
        persona.cedula = cedula_transitoria
        self._persona_repository.guardar(persona)
        inicio_foro = datetime.now(UTC)
        registros_foro: list[RegistroForoDTO] = []
        fuente_foro = None
        try:
            consulta_foro = self._foro_abogados.buscar_por_cedula(cedula_transitoria)
            registros_foro = await consulta_foro if inspect.isawaitable(consulta_foro) else consulta_foro
            fuente_foro = "foro_abogados"
        except GovDataError as exc:
            self._auditoria.registrar_fallido(
                str(trabajo.id), TipoPasoPipeline.FORO, sanitizar_error_externo(exc), inicio_foro, datetime.now(UTC)
            )
            self._cola.marcar_error(trabajo, "FORO_UNAVAILABLE")
        else:
            self._auditoria.registrar_ejecutado(
                str(trabajo.id), TipoPasoPipeline.FORO, inicio_foro, datetime.now(UTC), len(registros_foro)
            )
            self._cola.marcar_completado(trabajo)
        finally:
            cedula_transitoria = None
        
        return self._construir_resultado_completo(
            trabajo=trabajo,
            info_funcionario=info_funcionario,
            resultado=resultado,
            registros_foro=registros_foro,
            fuente_foro=fuente_foro,
        )

    def _construir_info_funcionario(self, persona: Persona) -> dict[str, str | None]:
        """Construye la información del funcionario desde la Persona y su cargo vigente."""
        # La información de cargo/dependencia/institución viene del endpoint
        # Aquí solo devolvemos los datos de contacto de la persona
        return {
            "correo_institucional": str(persona.correo) if persona.correo else None,
            "telefono_institucional": str(persona.telefono) if persona.telefono else None,
        }

    def _construir_resultado_error(
        self, 
        trabajo: Any, 
        info_funcionario: dict, 
        estado: str, 
        detalle: str
    ) -> ResultadoValidacionAbogado:
        return ResultadoValidacionAbogado(
            job_id=str(trabajo.id),
            estado=estado,
            institucion="",
            cargo="",
            dependencia="",
            correo_institucional=info_funcionario.get("correo_institucional"),
            telefono_institucional=info_funcionario.get("telefono_institucional"),
            ciudad=None,
            estado_identificacion=estado,
            confianza=0.0,
            detalle=detalle,
            fuente="consultas_ecuador",
            fecha_consulta=datetime.now(UTC),
        )

    def _construir_resultado_sin_identificacion(
        self, 
        trabajo: Any, 
        info_funcionario: dict, 
        resultado: ResultadoMatchingCedulaDTO
    ) -> ResultadoValidacionAbogado:
        return ResultadoValidacionAbogado(
            job_id=str(trabajo.id),
            estado=resultado.estado.value,
            institucion="",
            cargo="",
            dependencia="",
            correo_institucional=info_funcionario.get("correo_institucional"),
            telefono_institucional=info_funcionario.get("telefono_institucional"),
            ciudad=None,
            estado_identificacion=resultado.estado.value,
            confianza=resultado.confianza,
            fuente="consultas_ecuador",
            fecha_consulta=datetime.now(UTC),
            detalle=f"Identificación: {resultado.estado.value}",
        )

    def _construir_resultado_completo(
        self,
        trabajo: Any,
        info_funcionario: dict,
        resultado: ResultadoMatchingCedulaDTO,
        registros_foro: list[RegistroForoDTO],
        fuente_foro: str | None,
    ) -> ResultadoValidacionAbogado:
        # Extraer información del primer registro del Foro (si existe)
        registro_foro = registros_foro[0] if registros_foro else None
        
        # Información profesional consolidada
        info_profesional_parts = []
        if registro_foro:
            if registro_foro.registro:
                info_profesional_parts.append(f"Registro: {registro_foro.registro}")
            if registro_foro.estado:
                info_profesional_parts.append(f"Estado: {registro_foro.estado}")
            if registro_foro.provincia:
                info_profesional_parts.append(f"Provincia: {registro_foro.provincia}")
        info_profesional = " | ".join(info_profesional_parts) if info_profesional_parts else None
        
        return ResultadoValidacionAbogado(
            job_id=str(trabajo.id),
            estado=resultado.estado.value,
            institucion="",  # Se llena en el endpoint
            cargo="",        # Se llena en el endpoint
            dependencia="",  # Se llena en el endpoint
            correo_institucional=info_funcionario.get("correo_institucional"),
            telefono_institucional=info_funcionario.get("telefono_institucional"),
            ciudad=None,
            estado_identificacion=resultado.estado.value,
            confianza=resultado.confianza,
            cedula=resultado.candidato.cedula if resultado.candidato else None,
            registro_foro=registro_foro.registro if registro_foro else None,
            estado_foro=registro_foro.estado if registro_foro else None,
            provincia_foro=registro_foro.provincia if registro_foro else None,
            correo_personal=registro_foro.correo if registro_foro else None,
            celular_personal=registro_foro.celular if registro_foro else None,
            fuente=fuente_foro or "consultas_ecuador",
            fecha_consulta=datetime.now(UTC),
            detalle=f"Identificación: {resultado.estado.value}" + (f" | Foro: {info_profesional}" if info_profesional else ""),
        )
