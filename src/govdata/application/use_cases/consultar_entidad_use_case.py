"""Caso de uso: ConsultarEntidadUseCase -- EL FLUJO OBLIGATORIO completo
del Modulo 8:

    Portal Transparencia -> Extraer funcionarios -> Filtrar area juridica
    -> SENESCYT -> Obtener Cedula -> Foro de Abogados -> Extraer
    informacion profesional -> Fusionar -> Guardar historial -> Mostrar
    resultado

"NO EXISTEN FLUJOS ALTERNOS" -- este caso de uso ejecuta las 10 etapas en
ese orden exacto, para CADA funcionario del area juridica de la Entidad
consultada, sin desviarse. Cada etapa reutiliza infraestructura ya
congelada sin modificarla:

    - Portal Transparencia / Extraer funcionarios: `EntidadRepositoryPort`
      + `FuncionarioRepositoryPort` (Modulo 4).
    - Filtrar area juridica: `AreaRelevante.JURIDICA` (Modulo 1/4) sobre
      `Funcionario.area_clasificada` (ya clasificado por el Modulo 4).
    - Resolver Persona Master + SENESCYT: `ResolverOCrearPersonaMasterUseCase`
      (Modulo 6) + `EnriquecimientoAcademicoService` (Modulo 7).
    - Obtener Cedula: `Persona.cedula` (Modulo 1, ya existente).
    - Foro de Abogados / Extraer informacion profesional / Guardar
      historial: `EnriquecimientoForoService` (Modulo 8, este modulo --
      el versionado/historial ya sucede DENTRO de este servicio).
    - Fusionar / Mostrar resultado: se ensambla aqui mismo el
      `FuncionarioConsolidadoDTO` plano (Submodulo 8.11).

Un funcionario que falla en cualquier etapa NUNCA detiene a los demas --
mismo principio de aislamiento por item que `EnriquecerMasivoAcademicoUseCase`
(Modulo 7) y `MonitoreoContinuoService.monitorear_masiva` (Modulo 5)."""

from __future__ import annotations

from govdata.application.dto.funcionario_consolidado_dto import FuncionarioConsolidadoDTO
from govdata.application.dto.resultado_consulta_entidad_dto import ResultadoConsultaEntidadDTO
from govdata.application.ports.entidad_repository_port import EntidadRepositoryPort
from govdata.application.ports.funcionario_repository_port import FuncionarioRepositoryPort
from govdata.application.ports.persona_repository_port import PersonaRepositoryPort
from govdata.application.ports.registro_foro_repository_port import RegistroForoRepositoryPort
from govdata.application.services.enriquecimiento_academico_service import (
    EnriquecimientoAcademicoService,
)
from govdata.application.services.enriquecimiento_foro_service import EnriquecimientoForoService
from govdata.application.services.identity_resolution_service import senales_desde_persona_master
from govdata.application.services.job_manager_service import JobManagerService
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.config.logging_config import get_logger
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.job import JobStatus, TipoJob
from govdata.domain.exceptions.domain_exceptions import EntidadNoEncontradaError, GovDataError
from govdata.domain.value_objects.area_relevante import AreaRelevante

logger = get_logger(__name__)


class ConsultarEntidadUseCase:
    def __init__(
        self,
        entidad_repository: EntidadRepositoryPort,
        funcionario_repository: FuncionarioRepositoryPort,
        persona_repository: PersonaRepositoryPort,
        registro_foro_repository: RegistroForoRepositoryPort,
        resolver_persona_master_use_case: ResolverOCrearPersonaMasterUseCase,
        enriquecimiento_academico_service: EnriquecimientoAcademicoService,
        enriquecimiento_foro_service: EnriquecimientoForoService,
        job_manager: JobManagerService,
    ) -> None:
        self._entidad_repository = entidad_repository
        self._funcionario_repository = funcionario_repository
        self._persona_repository = persona_repository
        self._registro_foro_repository = registro_foro_repository
        self._resolver_persona_master_use_case = resolver_persona_master_use_case
        self._enriquecimiento_academico_service = enriquecimiento_academico_service
        self._enriquecimiento_foro_service = enriquecimiento_foro_service
        self._job_manager = job_manager

    def ejecutar(self, nombre_entidad: str) -> ResultadoConsultaEntidadDTO:
        # -- Portal Transparencia --------------------------------------
        entidad = self._entidad_repository.buscar_por_nombre(nombre_entidad)
        if entidad is None or entidad.id is None:
            raise EntidadNoEncontradaError(f"Entidad no encontrada en Transparencia: '{nombre_entidad}'")

        job = self._job_manager.crear_job(TipoJob.CONSULTA_FILTROS, entidad_id=entidad.id)
        job = self._job_manager.transicionar(job, JobStatus.EN_COLA)

        # -- Extraer funcionarios -> Filtrar area juridica ---------------
        job = self._job_manager.transicionar(job, JobStatus.DESCUBRIENDO)
        funcionarios = self._funcionario_repository.listar_por_entidad(entidad.id, solo_vigentes=True)
        juridicos = [f for f in funcionarios if f.area_clasificada == AreaRelevante.JURIDICA]

        job = self._job_manager.transicionar(job, JobStatus.CONSULTANDO_SENESCYT)
        job = self._job_manager.transicionar(job, JobStatus.CONSULTANDO_FORO)

        resultado: list[FuncionarioConsolidadoDTO] = []
        hubo_error = False
        for funcionario in juridicos:
            try:
                consolidado = self._procesar_funcionario(funcionario, entidad.nombre, str(job.id))
                if consolidado is not None:
                    resultado.append(consolidado)
            except GovDataError as exc:
                hubo_error = True
                logger.warning(
                    "consulta_entidad_item_fallo", entidad=entidad.nombre, persona_id=funcionario.persona_id, error=str(exc)
                )
                continue

        if hubo_error:
            self._job_manager.marcar_error(job, "Uno o mas funcionarios fallaron durante la consulta de la Entidad")
        else:
            job = self._job_manager.transicionar(job, JobStatus.EXTRAYENDO)  # "EXTRAYENDO_FORO" (8.14)
            job = self._job_manager.transicionar(job, JobStatus.GUARDANDO)  # "FUSIONANDO" (8.14)
            self._job_manager.finalizar(job)

        logger.info("consulta_entidad_completada", entidad=entidad.nombre, cantidad_funcionarios=len(resultado))
        return ResultadoConsultaEntidadDTO(funcionarios=resultado)

    def _procesar_funcionario(
        self, funcionario: Funcionario, entidad_nombre: str, job_id: str
    ) -> FuncionarioConsolidadoDTO | None:
        persona = self._persona_repository.buscar_por_id(funcionario.persona_id)
        if persona is None:
            logger.warning("consulta_entidad_persona_no_encontrada", persona_id=funcionario.persona_id)
            return None

        cargo_texto = str(funcionario.cargo)
        # -- Resolver Persona Master -> SENESCYT -------------------------
        persona_master = self._resolver_persona_master_use_case.ejecutar(
            persona, cargo=cargo_texto, institucion=entidad_nombre
        )
        senales = senales_desde_persona_master(persona_master, cargo=cargo_texto, institucion=entidad_nombre)
        self._enriquecimiento_academico_service.enriquecer(persona_master, senales)

        # -- Obtener Cedula -> Foro de Abogados -> Extraer info ----------
        # -- profesional -> Guardar historial (dentro del servicio) ------
        if persona_master.id is None:  # pragma: no cover -- garantizado por el resolver
            return None
        self._enriquecimiento_foro_service.enriquecer(persona_master, persona, job_id=job_id)

        # -- Fusionar -----------------------------------------------------
        registros_foro = self._registro_foro_repository.listar_vigentes_por_persona_master(persona_master.id)
        registro_foro = registros_foro[0] if registros_foro else None

        telefono_institucional = str(persona_master.telefono_principal) if persona_master.telefono_principal else None

        return FuncionarioConsolidadoDTO(
            nombre_completo=persona_master.nombre_completo.nombre_completo,
            cedula=persona.cedula,
            correo=str(persona_master.correo_principal) if persona_master.correo_principal else None,
            telefono=telefono_institucional,
            extension_telefonica=persona.extension_telefonica,
            celular=registro_foro.celular_personal if registro_foro else None,
            correo_personal=registro_foro.correo_personal if registro_foro else None,
            cargo=cargo_texto,
            dependencia=funcionario.dependencia,
            registro_foro=registro_foro.registro if registro_foro else None,
            estado_foro=registro_foro.estado.value if registro_foro else None,
            provincia_foro=registro_foro.provincia if registro_foro else None,
            fecha_consulta=registro_foro.fecha_consulta.isoformat() if registro_foro and registro_foro.fecha_consulta else None,
        )
