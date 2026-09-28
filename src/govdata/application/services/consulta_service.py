"""Servicio: ConsultaService -- Submodulos 4.5, 4.6, 4.7.

Punto de entrada UNICO para todas las formas de consulta (individual,
masiva, por filtros). `consultar_masiva` y `consultar_con_filtros`
reutilizan literalmente `consultar_entidad` / `FuncionarioRepositoryPort`
-- ninguna logica de pipeline se duplica.

Flujo de `consultar_entidad` (Submodulo 4.5):

    ¿Cache vigente? --si--> devolver lo ya persistido
           |no
           v
    Descubrir (Modulo 2) -> Descargar (Modulo 3, si hace falta)
           |
    ¿La version actual ya tiene extraccion? --si--> devolver lo ya persistido
           |no
           v
    Extraer (Modulo 4) -> devolver el contrato unificado

Cada consulta individual (llamada directa o disparada desde una masiva)
genera su propio `Job` -- el Job Manager traza el progreso real de CADA
entidad, no solo del lote.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from govdata.application.dto.filtros_consulta_dto import FiltrosConsultaDTO
from govdata.application.dto.resultado_unificado_dto import (
    DocumentoResumenDTO,
    EntidadResumenDTO,
    FuncionarioUnificadoDTO,
    ResultadoUnificadoDTO,
)
from govdata.application.ports.descarga_port import DescargaPort
from govdata.application.ports.descubrimiento_port import DescubrimientoPort
from govdata.application.ports.entidad_repository_port import EntidadRepositoryPort
from govdata.application.ports.extraccion_port import ExtraccionPort
from govdata.application.ports.funcionario_repository_port import FuncionarioRepositoryPort
from govdata.application.ports.persona_repository_port import PersonaRepositoryPort
from govdata.application.services.cache_service import CacheService
from govdata.application.services.job_manager_service import JobManagerService
from govdata.config.logging_config import get_logger
from govdata.domain.entities.documento import DocumentoTransparencia
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.job import Job, JobStatus, TipoJob
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import (
    DocumentoNoSoportadoError,
    GovDataError,
    PublicacionNoDisponibleError,
)

logger = get_logger(__name__)


class ConsultaService:
    def __init__(
        self,
        entidad_repository: EntidadRepositoryPort,
        funcionario_repository: FuncionarioRepositoryPort,
        persona_repository: PersonaRepositoryPort,
        cache_service: CacheService,
        job_manager: JobManagerService,
        descubrimiento: DescubrimientoPort,
        descarga: DescargaPort,
        extraccion: ExtraccionPort,
    ) -> None:
        self._entidad_repository = entidad_repository
        self._funcionario_repository = funcionario_repository
        self._persona_repository = persona_repository
        self._cache_service = cache_service
        self._job_manager = job_manager
        self._descubrimiento = descubrimiento
        self._descarga = descarga
        self._extraccion = extraccion

    # -- Submodulo 4.5: consulta individual --------------------------------

    def consultar_entidad(self, entidad: Entidad) -> ResultadoUnificadoDTO:
        job = self._job_manager.crear_job(TipoJob.CONSULTA_INDIVIDUAL, entidad_id=entidad.id)
        try:
            resultado = self._ejecutar_pipeline(entidad, job)
            self._job_manager.finalizar(job)
            return resultado
        except GovDataError as exc:
            self._job_manager.marcar_error(job, str(exc))
            raise

    def _ejecutar_pipeline(self, entidad: Entidad, job: Job) -> ResultadoUnificadoDTO:
        self._job_manager.transicionar(job, JobStatus.DESCUBRIENDO)
        resultado_descubrimiento = self._descubrimiento.descubrir(entidad)
        if not resultado_descubrimiento.exito or resultado_descubrimiento.publicacion is None:
            raise PublicacionNoDisponibleError(
                resultado_descubrimiento.error or f"Sin publicacion disponible para '{entidad.nombre}'"
            )

        publicacion = resultado_descubrimiento.publicacion
        documento = resultado_descubrimiento.documento
        if documento is None:
            raise DocumentoNoSoportadoError(
                resultado_descubrimiento.error or f"Sin documento disponible para '{entidad.nombre}'"
            )

        decision_cache = self._cache_service.evaluar_entidad(entidad.id, publicacion.mes_publicado)  # type: ignore[arg-type]
        if decision_cache.vigente and decision_cache.documento is not None:
            logger.info("consulta_servida_desde_cache", entidad=entidad.nombre, motivo=decision_cache.motivo)
            self._job_manager.transicionar(job, JobStatus.GUARDANDO, mensaje="cache_vigente")
            return self._construir_desde_persistencia(entidad, decision_cache.documento, publicacion.mes_publicado)

        self._job_manager.transicionar(job, JobStatus.DESCARGANDO)
        documento = self._descarga.descargar(documento)

        if not self._cache_service.requiere_reextraccion(documento.id):  # type: ignore[arg-type]
            logger.info("extraccion_ya_vigente_para_version_actual", entidad=entidad.nombre, version=documento.version)
            self._job_manager.transicionar(job, JobStatus.GUARDANDO, mensaje="extraccion_ya_vigente")
            return self._construir_desde_persistencia(entidad, documento, publicacion.mes_publicado)

        self._job_manager.transicionar(job, JobStatus.EXTRAYENDO)
        resultado = self._extraccion.extraer(entidad, documento, publicacion.mes_publicado)
        self._job_manager.transicionar(job, JobStatus.GUARDANDO)
        return resultado

    def _construir_desde_persistencia(
        self, entidad: Entidad, documento: DocumentoTransparencia, mes_publicado: date
    ) -> ResultadoUnificadoDTO:
        funcionarios = self._funcionario_repository.listar_por_documento(documento.id)  # type: ignore[arg-type]
        dtos = [dto for f in funcionarios if (dto := self._a_dto(f)) is not None]
        return ResultadoUnificadoDTO(
            entidad=self._entidad_resumen(entidad),
            documento=self._documento_resumen(documento, mes_publicado),
            funcionarios=dtos,
            generado_en=datetime.now(UTC),
        )

    def _a_dto(self, funcionario: Funcionario) -> FuncionarioUnificadoDTO | None:
        persona: Persona | None = self._persona_repository.buscar_por_id(funcionario.persona_id)
        if persona is None:
            return None
        return FuncionarioUnificadoDTO(
            nombre=persona.nombre_completo.nombres,
            apellido=persona.nombre_completo.apellidos,
            cargo=str(funcionario.cargo),
            dependencia=funcionario.dependencia,
            correo=str(persona.correo) if persona.correo else None,
            telefono=str(persona.telefono) if persona.telefono else None,
            area=funcionario.area_clasificada.value,
            score=round(funcionario.score_clasificacion or 0.0, 2),
            fingerprint=persona.fingerprint or "",
        )

    @staticmethod
    def _entidad_resumen(entidad: Entidad) -> EntidadResumenDTO:
        return EntidadResumenDTO(
            id=entidad.id,  # type: ignore[arg-type]
            nombre=entidad.nombre,
            portal_origen=entidad.portal_origen,
            identificador_portal=entidad.metadata_extra.get("identificador_portal"),
        )

    @staticmethod
    def _documento_resumen(documento: DocumentoTransparencia, mes_publicado: date) -> DocumentoResumenDTO:
        return DocumentoResumenDTO(
            id=documento.id,  # type: ignore[arg-type]
            tipo_archivo=documento.tipo_archivo.value,
            mes_publicado=mes_publicado,
            hash_sha256=documento.hash_sha256 or "",
            version=documento.version,
            url=documento.url_documento,
        )

    # -- Submodulo 4.6: consulta masiva -------------------------------------

    def consultar_masiva(self, entidades: list[Entidad] | None = None) -> list[ResultadoUnificadoDTO]:
        """`entidades=None` -> TODAS las entidades activas. Reutiliza
        `consultar_entidad` por cada una -- ningun pipeline duplicado."""
        objetivo = entidades if entidades is not None else self._entidad_repository.listar_activas()
        job = self._job_manager.crear_job(TipoJob.CONSULTA_MASIVA)
        self._job_manager.transicionar(job, JobStatus.EN_COLA)

        resultados: list[ResultadoUnificadoDTO] = []
        for entidad in objetivo:
            try:
                resultados.append(self.consultar_entidad(entidad))
            except GovDataError as exc:
                logger.warning("consulta_masiva_entidad_fallida", entidad=entidad.nombre, error=str(exc))
                self._job_manager.registrar_reintento(job)
                continue

        self._job_manager.finalizar(job)
        logger.info("consulta_masiva_finalizada", total=len(objetivo), exitosas=len(resultados))
        return resultados

    # -- Submodulo 4.7: consulta por filtros --------------------------------

    def consultar_con_filtros(self, filtros: FiltrosConsultaDTO) -> list[FuncionarioUnificadoDTO]:
        """Consulta de SOLO LECTURA sobre lo ya persistido -- nunca dispara
        descubrimiento/descarga/extraccion nueva."""
        funcionarios = self._funcionario_repository.buscar_con_filtros(filtros)
        return [dto for f in funcionarios if (dto := self._a_dto(f)) is not None]
