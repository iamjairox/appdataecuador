"""Caso de uso: ConsultarPersonaForoUseCase -- Submodulo 8.12 (Consulta
Individual: `consultar_persona()`).

Orquesta el tramo final del flujo obligatorio del Modulo 8:

    ... -> SENESCYT -> Obtener Cedula -> Foro de Abogados -> Extraer
    informacion profesional -> Fusionar -> Guardar historial -> Mostrar
    resultado

"Resolver Persona Master" (Modulo 6, `ResolverOCrearPersonaMasterUseCase`,
REUTILIZADO) y "Consultar SENESCYT" (Modulo 7, `EnriquecimientoAcademicoService`,
REUTILIZADO) ya sucedieron o suceden aqui antes del tramo del Foro -- la
cedula "ya conocida" para consultar el Foro es `persona.cedula` (Modulo 1,
campo ya existente; ver `ForoAbogadosPort` para la justificacion completa
de esta decision de diseno).

El resultado es el Contrato Oficial (Submodulo 8.16): `{"entidad": "",
"documento": "", "funcionario": {}, "senescyt": {}, "foro": {}}`.

Job Manager (Modulo 4, REUTILIZADO): los estados `CONSULTANDO_FORO` (ya
existente en `JobStatus`, placeholder previsor igual que
`CONSULTANDO_SENESCYT` en Modulo 7) y `FINALIZADO` se usan directo;
`EXTRAYENDO_FORO`/`FUSIONANDO` (Submodulo 8.14, nuevos nombres que
`JobStatus` -- congelado -- no admite) se mapean a los estados genericos
mas cercanos ya existentes: `EXTRAYENDO` y `GUARDANDO` respectivamente --
mismo criterio documentado que Modulo 7 con COMPARANDO/ACTUALIZANDO."""

from __future__ import annotations

from govdata.application.dto.contrato_consulta_funcionario_dto import (
    ContratoConsultaFuncionarioDTO,
)
from govdata.application.services.enriquecimiento_academico_service import (
    EnriquecimientoAcademicoService,
)
from govdata.application.services.enriquecimiento_foro_service import EnriquecimientoForoService
from govdata.application.services.identity_resolution_service import senales_desde_persona_master
from govdata.application.services.job_manager_service import JobManagerService
from govdata.application.services.perfil_academico_service import PerfilAcademicoService
from govdata.application.services.perfil_consolidado_service import PerfilConsolidadoService
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.domain.entities.job import JobStatus, TipoJob
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import GovDataError, PersonaMasterInvalidaError


class ConsultarPersonaForoUseCase:
    def __init__(
        self,
        resolver_persona_master_use_case: ResolverOCrearPersonaMasterUseCase,
        enriquecimiento_academico_service: EnriquecimientoAcademicoService,
        enriquecimiento_foro_service: EnriquecimientoForoService,
        perfil_academico_service: PerfilAcademicoService,
        perfil_consolidado_service: PerfilConsolidadoService,
        job_manager: JobManagerService,
    ) -> None:
        self._resolver_persona_master_use_case = resolver_persona_master_use_case
        self._enriquecimiento_academico_service = enriquecimiento_academico_service
        self._enriquecimiento_foro_service = enriquecimiento_foro_service
        self._perfil_academico_service = perfil_academico_service
        self._perfil_consolidado_service = perfil_consolidado_service
        self._job_manager = job_manager

    def ejecutar(
        self, persona: Persona, entidad_nombre: str = "", cargo: str | None = None, institucion: str | None = None
    ) -> ContratoConsultaFuncionarioDTO:
        job = self._job_manager.crear_job(TipoJob.CONSULTA_INDIVIDUAL)
        job = self._job_manager.transicionar(job, JobStatus.EN_COLA)
        try:
            persona_master = self._resolver_persona_master_use_case.ejecutar(persona, cargo=cargo, institucion=institucion)

            job = self._job_manager.transicionar(job, JobStatus.CONSULTANDO_SENESCYT)
            senales = senales_desde_persona_master(persona_master, cargo=cargo, institucion=institucion)
            self._enriquecimiento_academico_service.enriquecer(persona_master, senales)

            job = self._job_manager.transicionar(job, JobStatus.CONSULTANDO_FORO)
            resultado_foro = self._enriquecimiento_foro_service.enriquecer(persona_master, persona, job_id=str(job.id))

            if resultado_foro.error is not None:
                self._job_manager.marcar_error(job, resultado_foro.error)
            else:
                job = self._job_manager.transicionar(job, JobStatus.EXTRAYENDO)  # "EXTRAYENDO_FORO" (8.14)
                job = self._job_manager.transicionar(job, JobStatus.GUARDANDO)  # "FUSIONANDO" (8.14)
                self._job_manager.finalizar(job)

            if persona_master.id is None:
                raise PersonaMasterInvalidaError("PersonaMaster resuelta sin id -- inesperado tras persistirla")
            senescyt_dict = self._perfil_academico_service.construir_perfil(persona_master.id).to_dict()
            foro_dict = self._perfil_consolidado_service.construir_foro(persona_master.id)

            funcionario_dict = {
                "nombre_completo": persona_master.nombre_completo.nombre_completo,
                "cedula": persona.cedula,
                "correo": str(persona_master.correo_principal) if persona_master.correo_principal else None,
                "telefono": str(persona_master.telefono_principal) if persona_master.telefono_principal else None,
                "cargo": cargo,
                "dependencia": institucion,
            }
            return ContratoConsultaFuncionarioDTO(
                entidad=entidad_nombre, documento=persona.cedula or "", funcionario=funcionario_dict,
                senescyt=senescyt_dict, foro=foro_dict,
            )
        except GovDataError as exc:
            self._job_manager.marcar_error(job, str(exc))
            raise
