"""Contenedor de Inyeccion de Dependencias.

Arma el grafo de objetos de la aplicacion (settings -> logging -> engine ->
session factory -> repositorios -> casos de uso -> servicios) en un solo
lugar. Los casos de uso y servicios reciben sus dependencias por
constructor; nadie mas que este Container instancia adaptadores
concretos (Playwright, SQLAlchemy).

Deliberadamente simple (sin libreria externa tipo `dependency-injector`):
un conjunto de propiedades/metodos `lazy` sobre `Settings`. Si la cantidad
de adaptadores crece mucho en modulos posteriores, este es el punto de
extension natural para migrar a un framework de DI si hiciera falta -- el
resto del sistema no lo notaria porque solo conoce `Container`.
"""

from __future__ import annotations

# -- Modulo 7: Adaptador SENESCYT + Enriquecimiento Academico -- imports --
# -- agregados de forma aditiva (nunca se toca una linea de las --
# -- importaciones de arriba, Modulos 1-6 congelados). ---------------------
import os
from contextlib import AbstractContextManager
from functools import cached_property

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

# -- Modulo 9: Orquestador Maestro del Sistema GovData -- imports --------
# -- agregados de forma aditiva (nunca se toca una linea de las ----------
# -- importaciones de arriba, Modulos 1-8 congelados). --------------------
from govdata.application.dto.resultado_orquestacion_dto import ResultadoOrquestacionDTO
from govdata.application.ports.descarga_worker_port import DescargaWorkerPort
from govdata.application.ports.entidad_worker_port import EntidadWorkerPort
from govdata.application.ports.file_storage_port import FileStoragePort
from govdata.application.ports.verificacion_remota_port import VerificacionRemotaPort
from govdata.application.services.alerta_academica_service import AlertaAcademicaService

# -- Modulo 8: Motor de Consulta al Foro de Abogados, Fusion de Datos y --
# -- Perfil Consolidado del Funcionario -- imports agregados de forma ----
# -- aditiva (nunca se toca una linea de las importaciones de arriba, ----
# -- Modulos 1-7 congelados). ----------------------------------------------
from govdata.application.services.alerta_foro_service import AlertaForoService

# -- Modulo 6: Motor de Identidad, Enriquecimiento de Personas y Fuentes --
# -- Externas -- imports agregados de forma aditiva (nunca se toca una --
# -- linea de las importaciones de arriba, Modulos 1-5 congelados). ------
from govdata.application.services.alerta_perfil_service import AlertaPerfilService
from govdata.application.services.alerta_service import AlertaService
from govdata.application.services.auditoria_comparacion_service import AuditoriaComparacionService
from govdata.application.services.auditoria_consulta_fuente_service import (
    AuditoriaConsultaFuenteService,
)
from govdata.application.services.auditoria_orquestacion_service import AuditoriaOrquestacionService
from govdata.application.services.cache_foro_service import CacheForoService
from govdata.application.services.cache_fuente_service import CacheFuenteService
from govdata.application.services.cache_senescyt_service import CacheSenescytService
from govdata.application.services.cache_service import CacheService
from govdata.application.services.cola_trabajos_orquestador_service import (
    ColaTrabajosOrquestadorService,
)
from govdata.application.services.comparacion_academica_service import ComparacionAcademicaService
from govdata.application.services.comparacion_foro_service import ComparacionForoService
from govdata.application.services.consulta_foro_service import ConsultaForoService
from govdata.application.services.consulta_senescyt_service import ConsultaSenescytService
from govdata.application.services.consulta_service import ConsultaService
from govdata.application.services.dashboard_interno_service import DashboardInternoService
from govdata.application.services.descarga_orchestrator_service import DescargaOrchestratorService
from govdata.application.services.enriquecimiento_academico_service import (
    EnriquecimientoAcademicoService,
)
from govdata.application.services.enriquecimiento_foro_service import EnriquecimientoForoService
from govdata.application.services.enriquecimiento_service import EnriquecimientoService
from govdata.application.services.evento_academico_service import EventoAcademicoService
from govdata.application.services.evento_foro_service import EventoForoService
from govdata.application.services.evento_perfil_service import EventoPerfilService
from govdata.application.services.evento_service import EventoService
from govdata.application.services.fusion_service import FusionService
from govdata.application.services.govdata_pipeline_orchestrator import GovDataPipelineOrchestrator
from govdata.application.services.historial_service import HistorialService
from govdata.application.services.identity_resolution_service import IdentityResolutionService
from govdata.application.services.job_manager_service import JobManagerService
from govdata.application.services.metricas_academicas_service import MetricasAcademicasService
from govdata.application.services.metricas_foro_service import MetricasForoService
from govdata.application.services.monitoreo_continuo_service import MonitoreoContinuoService
from govdata.application.services.motor_estadisticas_service import MotorEstadisticasService
from govdata.application.services.motor_politicas_service import MotorPoliticasService
from govdata.application.services.oportunidad_comercial_service import OportunidadComercialService
from govdata.application.services.parser_factory import ParserFactory
from govdata.application.services.perfil_academico_service import PerfilAcademicoService
from govdata.application.services.perfil_consolidado_service import PerfilConsolidadoService
from govdata.application.services.perfil_persona_service import PerfilPersonaService
from govdata.application.services.persistencia_inteligente_service import (
    PersistenciaInteligenteService,
)
from govdata.application.services.pipeline_orchestrator_service import PipelineOrchestratorService
from govdata.application.services.priorizacion_service import PriorizacionService
from govdata.application.services.programador_enriquecimiento_service import (
    ProgramadorEnriquecimientoService,
)
from govdata.application.services.registro_foro_service import RegistroForoService
from govdata.application.services.registro_fuente_service import RegistroFuenteService
from govdata.application.services.timeline_persona_service import TimelinePersonaService
from govdata.application.services.timeline_service import TimelineService
from govdata.application.services.titulo_academico_service import TituloAcademicoService
from govdata.application.services.verificacion_service import VerificacionService
from govdata.application.use_cases.comparar_documentos_use_case import CompararDocumentosUseCase
from govdata.application.use_cases.consultar_entidad_use_case import ConsultarEntidadUseCase
from govdata.application.use_cases.consultar_masivo_foro_use_case import ConsultarMasivoForoUseCase
from govdata.application.use_cases.consultar_persona_foro_use_case import (
    ConsultarPersonaForoUseCase,
)
from govdata.application.use_cases.consultar_por_cedula_foro_use_case import (
    ConsultarPorCedulaForoUseCase,
)
from govdata.application.use_cases.enriquecer_masivo_academico_use_case import (
    EnriquecerMasivoAcademicoUseCase,
)
from govdata.application.use_cases.enriquecer_persona_academica_use_case import (
    EnriquecerPersonaAcademicaUseCase,
)
from govdata.application.use_cases.enriquecer_persona_use_case import EnriquecerPersonaUseCase
from govdata.application.use_cases.extraer_documento_use_case import ExtraerDocumentoUseCase
from govdata.application.use_cases.listar_entidades_api_use_case import ListarEntidadesApiUseCase
from govdata.application.use_cases.listar_entidades_use_case import ListarEntidadesUseCase
from govdata.application.use_cases.obtener_alertas_funcionario_use_case import (
    ObtenerAlertasFuncionarioUseCase,
)
from govdata.application.use_cases.obtener_cambios_entidad_use_case import (
    ObtenerCambiosEntidadUseCase,
)
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.config.logging_config import configurar_logging, get_logger
from govdata.config.rule_engine import cargar_rule_engine
from govdata.config.rule_engine_academico import cargar_rule_engine_academico
from govdata.config.rule_engine_foro import cargar_rule_engine_foro
from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad
from govdata.config.rule_engine_orquestador import cargar_rule_engine_orquestador
from govdata.config.settings import Settings, get_settings
from govdata.domain.entities.documento import DocumentoTransparencia
from govdata.domain.entities.entidad import Entidad
from govdata.domain.rules.reglas_academicas import ReglasCacheSenescyt, RuleEngineAcademico
from govdata.domain.rules.reglas_configurables import RuleEngine
from govdata.domain.rules.reglas_foro import ReglasCacheForo, RuleEngineForo
from govdata.domain.rules.reglas_identidad import RuleEngineIdentidad
from govdata.domain.rules.reglas_orquestador import PoliticaEjecucion, RuleEngineOrquestador
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador
from govdata.infrastructure.consulta.documento_descarga_adapter import DocumentoDescargaAdapter
from govdata.infrastructure.consulta.documento_extraccion_adapter import DocumentoExtraccionAdapter
from govdata.infrastructure.consulta.dpe_descubrimiento_adapter import DpeDescubrimientoAdapter
from govdata.infrastructure.http.documento_descarga_worker import DocumentoDescargaWorker
from govdata.infrastructure.http.foro_abogados_adapter import ForoAbogadosAdapter
from govdata.infrastructure.http.http_verificador_cambios_adapter import (
    HttpVerificadorCambiosAdapter,
)
from govdata.infrastructure.http.senescyt_adapter import SenescytAdapter
from govdata.infrastructure.parsers.csv.csv_parser import CsvParser
from govdata.infrastructure.parsers.excel.xls_parser import XlsParser
from govdata.infrastructure.parsers.excel.xlsx_parser import XlsxParser
from govdata.infrastructure.parsers.pdf.pdf_parser_engine import PdfParserEngine
from govdata.infrastructure.persistence.postgresql.database import (
    crear_engine,
    crear_session_factory,
    sesion_scope,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_academica_repository import (
    SqlAlchemyAlertaAcademicaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_foro_repository import (
    SqlAlchemyAlertaForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_perfil_repository import (
    SqlAlchemyAlertaPerfilRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_repository import (
    SqlAlchemyAlertaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_atributo_trazable_repository import (
    SqlAlchemyAtributoTrazableRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_auditoria_comparacion_repository import (
    SqlAlchemyAuditoriaComparacionRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_auditoria_etapa_repository import (
    SqlAlchemyAuditoriaEtapaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_caso_revision_identidad_repository import (
    SqlAlchemyCasoRevisionIdentidadRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_consulta_foro_repository import (
    SqlAlchemyConsultaForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_consulta_fuente_log_repository import (
    SqlAlchemyConsultaFuenteLogRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_consulta_senescyt_repository import (
    SqlAlchemyConsultaSenescytRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_documento_repository import (
    SqlAlchemyDocumentoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_entidad_repository import (
    SqlAlchemyEntidadRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_academico_repository import (
    SqlAlchemyEventoAcademicoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_foro_repository import (
    SqlAlchemyEventoForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_perfil_repository import (
    SqlAlchemyEventoPerfilRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_repository import (
    SqlAlchemyEventoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_funcionario_consulta_paginada_repository import (
    SqlAlchemyFuncionarioConsultaPaginadaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_funcionario_repository import (
    SqlAlchemyFuncionarioRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_historial_academico_repository import (
    SqlAlchemyHistorialAcademicoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_historial_foro_repository import (
    SqlAlchemyHistorialForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_job_repository import (
    SqlAlchemyJobRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_oportunidad_comercial_repository import (
    SqlAlchemyOportunidadComercialRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
    SqlAlchemyPersonaMasterRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_publicacion_repository import (
    SqlAlchemyPublicacionRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_registro_foro_repository import (
    SqlAlchemyRegistroForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_registro_foro_version_repository import (
    SqlAlchemyRegistroForoVersionRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_registro_fuente_repository import (
    SqlAlchemyRegistroFuenteRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_titulo_academico_repository import (
    SqlAlchemyTituloAcademicoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_titulo_version_academica_repository import (
    SqlAlchemyTituloVersionAcademicaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_trabajo_orquestador_repository import (
    SqlAlchemyTrabajoOrquestadorRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_verificacion_repository import (
    SqlAlchemyVerificacionRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_version_funcionario_repository import (
    SqlAlchemyVersionFuncionarioRepository,
)
from govdata.infrastructure.scraping.dpe_entidad_worker import DpeEntidadWorker
from govdata.infrastructure.scraping.playwright.browser_manager import BrowserManager
from govdata.infrastructure.scraping.playwright.dpe_scraper_adapter import DpeScraperAdapter
from govdata.infrastructure.scraping.rate_limiter import RateLimiter
from govdata.infrastructure.storage.local_file_storage_adapter import LocalFileStorageAdapter
from govdata.infrastructure.storage.minio_storage_adapter import MinioStorageAdapter


class Container:
    """Contenedor raiz de dependencias de la aplicacion."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings: Settings = settings or get_settings()
        configurar_logging(self.settings)
        self.logger = get_logger(__name__)
        self.logger.info("container_inicializado", entorno=self.settings.app_env)

    @cached_property
    def engine(self) -> Engine:
        return crear_engine(self.settings)

    @cached_property
    def session_factory(self) -> sessionmaker[Session]:
        return crear_session_factory(self.engine)

    def nueva_sesion(self) -> AbstractContextManager[Session]:
        """Retorna un context manager de sesion (Unit of Work) listo para usar.

        Uso:
            with container.nueva_sesion() as sesion:
                repo = SqlAlchemyEntidadRepository(sesion)
                ...
        """
        return sesion_scope(self.session_factory)

    @cached_property
    def rate_limiter(self) -> RateLimiter:
        """Rate limiter UNICO y compartido entre todos los workers/hilos:
        el limite es sobre el portal como un todo, no por hilo."""
        return RateLimiter(self.settings.scraping.intervalo_minimo_segundos)

    def descubrir_y_persistir_entidades(self) -> list[Entidad]:
        """Ejecuta el Paso 1 del Modulo 2: listar todas las entidades del
        portal y persistirlas. Se corre una sola vez, secuencial (no
        necesita concurrencia: es una unica llamada de red).
        """
        browser_manager = BrowserManager(self.settings.playwright)
        try:
            with browser_manager.nuevo_contexto() as contexto:
                adapter = DpeScraperAdapter(
                    contexto=contexto,
                    rate_limiter=self.rate_limiter,
                    url_origen=self.settings.scraping.url_origen_dpe,
                    max_reintentos=self.settings.scraping.max_reintentos,
                    backoff_base_segundos=self.settings.scraping.backoff_base_segundos,
                )
                with self.nueva_sesion() as sesion:
                    caso_uso = ListarEntidadesUseCase(
                        scraper=adapter, entidad_repository=SqlAlchemyEntidadRepository(sesion)
                    )
                    return caso_uso.ejecutar()
        finally:
            browser_manager.cerrar()

    def crear_pipeline_descubrimiento(self) -> PipelineOrchestratorService:
        """Arma el orquestador del Paso 2-6 del Modulo 2 (publicacion +
        documento por entidad, en paralelo)."""

        def _worker_factory() -> EntidadWorkerPort:
            return DpeEntidadWorker(
                session_factory=self.session_factory,
                playwright_settings=self.settings.playwright,
                scraping_settings=self.settings.scraping,
                rate_limiter=self.rate_limiter,
            )

        return PipelineOrchestratorService(
            worker_factory=_worker_factory,
            concurrencia_maxima=self.settings.scraping.concurrencia_maxima,
        )

    @cached_property
    def storage(self) -> FileStoragePort:
        """Backend de almacenamiento (Modulo 3), segun `STORAGE_BACKEND`.
        Se comparte entre todos los workers -- ver `DocumentoDescargaWorker`."""
        if self.settings.storage.backend == "minio":
            minio_settings = self.settings.minio
            return MinioStorageAdapter(
                endpoint=minio_settings.endpoint,
                access_key=minio_settings.access_key,
                secret_key=minio_settings.secret_key.get_secret_value(),
                bucket=minio_settings.bucket,
                usar_ssl=minio_settings.usar_ssl,
            )
        return LocalFileStorageAdapter(ruta_base=self.settings.storage.ruta_local)

    def listar_documentos_pendientes(self) -> list[DocumentoTransparencia]:
        """Paso 1 del Modulo 3: libera documentos estancados y lista los
        pendientes de descarga (cola persistida en BD, ver
        `DocumentoRepositoryPort`)."""
        with self.nueva_sesion() as sesion:
            repo = SqlAlchemyDocumentoRepository(sesion)
            liberados = repo.liberar_estancados(self.settings.download.minutos_liberar_estancados)
            if liberados:
                self.logger.warning("documentos_estancados_liberados", cantidad=liberados)
            return repo.listar_pendientes(self.settings.download.limite_lote)

    def crear_pipeline_descarga(self) -> DescargaOrchestratorService:
        """Arma el orquestador de descarga del Modulo 3."""

        def _worker_factory() -> DescargaWorkerPort:
            return DocumentoDescargaWorker(
                session_factory=self.session_factory,
                storage=self.storage,
                timeout_segundos=self.settings.download.timeout_segundos,
                max_reintentos=self.settings.download.max_reintentos,
                backoff_base_segundos=self.settings.download.backoff_base_segundos,
                tamano_maximo_bytes=self.settings.download.tamano_maximo_bytes,
            )

        return DescargaOrchestratorService(
            worker_factory=_worker_factory,
            concurrencia_maxima=self.settings.download.concurrencia_maxima,
        )

    # -- Modulo 4: Motor de Extraccion Inteligente --------------------------

    @cached_property
    def rule_engine(self) -> RuleEngine:
        """Motor de Reglas (YAML) -- sinonimos de normalizacion, catalogo
        de clasificacion por area, vigencia de cache. Una sola carga por
        proceso; los archivos viven en `config/rules/`."""
        return cargar_rule_engine()

    @cached_property
    def parser_factory(self) -> ParserFactory:
        """Fabrica de parsers (Submodulo 4.1, patron Strategy). Agregar un
        formato nuevo es agregar una clase a esta lista, nunca un `if`.
        Los parsers tabulares reciben los sinonimos de normalizacion para
        detectar la hoja y la fila de encabezado reales."""
        normalizacion = self.rule_engine.normalizacion
        return ParserFactory(
            parsers=[
                PdfParserEngine(),
                XlsxParser(normalizacion),
                XlsParser(normalizacion),
                CsvParser(normalizacion),
            ]
        )

    @staticmethod
    def buscar_entidad_por_nombre(sesion: Session, fragmento_nombre: str) -> Entidad | None:
        return SqlAlchemyEntidadRepository(sesion).buscar_por_nombre(fragmento_nombre)

    def crear_consulta_service(self, sesion: Session) -> ConsultaService:
        """Arma `ConsultaService` (Submodulos 4.5-4.7) ligado a `sesion`.

        La sesion vive tanto como dure la consulta completa (puede incluir
        descubrimiento+descarga+extraccion, potencialmente varios
        segundos) -- por eso el llamador es responsable de abrirla con
        `container.nueva_sesion()` y mantenerla durante toda la consulta,
        en vez de que este metodo cree una internamente.
        """
        entidad_repo = SqlAlchemyEntidadRepository(sesion)
        funcionario_repo = SqlAlchemyFuncionarioRepository(sesion)
        persona_repo = SqlAlchemyPersonaRepository(sesion)
        publicacion_repo = SqlAlchemyPublicacionRepository(sesion)
        documento_repo = SqlAlchemyDocumentoRepository(sesion)
        job_repo = SqlAlchemyJobRepository(sesion)

        cache_service = CacheService(
            publicacion_repository=publicacion_repo,
            documento_repository=documento_repo,
            funcionario_repository=funcionario_repo,
            reglas=self.rule_engine.cache,
        )
        job_manager = JobManagerService(job_repo)

        descubrimiento = DpeDescubrimientoAdapter(
            DpeEntidadWorker(
                session_factory=self.session_factory,
                playwright_settings=self.settings.playwright,
                scraping_settings=self.settings.scraping,
                rate_limiter=self.rate_limiter,
            )
        )
        descarga = DocumentoDescargaAdapter(
            DocumentoDescargaWorker(
                session_factory=self.session_factory,
                storage=self.storage,
                timeout_segundos=self.settings.download.timeout_segundos,
                max_reintentos=self.settings.download.max_reintentos,
                backoff_base_segundos=self.settings.download.backoff_base_segundos,
                tamano_maximo_bytes=self.settings.download.tamano_maximo_bytes,
            )
        )
        extraccion = DocumentoExtraccionAdapter(
            caso_uso=ExtraerDocumentoUseCase(
                parser_factory=self.parser_factory,
                rule_engine=self.rule_engine,
                persona_repository=persona_repo,
                funcionario_repository=funcionario_repo,
            ),
            storage=self.storage,
        )

        return ConsultaService(
            entidad_repository=entidad_repo,
            funcionario_repository=funcionario_repo,
            persona_repository=persona_repo,
            cache_service=cache_service,
            job_manager=job_manager,
            descubrimiento=descubrimiento,
            descarga=descarga,
            extraccion=extraccion,
        )

    # -- Modulo 5: Motor de Persistencia Inteligente, Historial, Deteccion --
    # -- de Cambios y Alertas -------------------------------------------------

    @cached_property
    def verificacion_remota(self) -> VerificacionRemotaPort:
        """Chequeo HTTP HEAD liviano (Submodulo 5.15) -- deliberadamente
        SEPARADO de `HttpFetcherPort` (Modulo 3): no le agrega ni cambia
        ningun metodo, para no tocar el comportamiento ya aprobado."""
        return HttpVerificadorCambiosAdapter()

    def crear_monitoreo_service(self, sesion: Session) -> MonitoreoContinuoService:
        """Arma `MonitoreoContinuoService` (Submodulo 5.15) ligado a `sesion`.

        Misma convencion que `crear_consulta_service` (Modulo 4): el
        llamador abre la sesion con `container.nueva_sesion()` y la
        mantiene viva durante todo el monitoreo (puede incluir
        descubrimiento+descarga+extraccion+comparacion).

        Nota de diseno: el bloque de construccion de
        `descubrimiento`/`descarga`/`extraccion` de aqui abajo es
        deliberadamente muy similar al de `crear_consulta_service` --
        se duplica a proposito en vez de extraer un helper compartido,
        porque `crear_consulta_service` es codigo del Modulo 4 ya
        aprobado que esta instruccion explicita prohibe modificar.
        """
        entidad_repo = SqlAlchemyEntidadRepository(sesion)
        publicacion_repo = SqlAlchemyPublicacionRepository(sesion)
        documento_repo = SqlAlchemyDocumentoRepository(sesion)
        funcionario_repo = SqlAlchemyFuncionarioRepository(sesion)
        persona_repo = SqlAlchemyPersonaRepository(sesion)
        version_repo = SqlAlchemyVersionFuncionarioRepository(sesion)
        alerta_repo = SqlAlchemyAlertaRepository(sesion)
        evento_repo = SqlAlchemyEventoRepository(sesion)
        auditoria_repo = SqlAlchemyAuditoriaComparacionRepository(sesion)
        oportunidad_repo = SqlAlchemyOportunidadComercialRepository(sesion)
        verificacion_repo = SqlAlchemyVerificacionRepository(sesion)

        historial_service = HistorialService(version_repo)
        persistencia_service = PersistenciaInteligenteService(persona_repo, funcionario_repo, historial_service)
        alerta_service = AlertaService(alerta_repo, self.rule_engine.criticidad)
        oportunidad_service = OportunidadComercialService(oportunidad_repo, self.rule_engine.criticidad)
        evento_service = EventoService(evento_repo)
        auditoria_service = AuditoriaComparacionService(auditoria_repo)
        verificacion_service = VerificacionService(verificacion_repo)

        comparar_documentos = CompararDocumentosUseCase(
            persistencia_service=persistencia_service,
            alerta_service=alerta_service,
            oportunidad_service=oportunidad_service,
            evento_service=evento_service,
            auditoria_service=auditoria_service,
            rule_engine=self.rule_engine,
        )

        descubrimiento = DpeDescubrimientoAdapter(
            DpeEntidadWorker(
                session_factory=self.session_factory,
                playwright_settings=self.settings.playwright,
                scraping_settings=self.settings.scraping,
                rate_limiter=self.rate_limiter,
            )
        )
        descarga = DocumentoDescargaAdapter(
            DocumentoDescargaWorker(
                session_factory=self.session_factory,
                storage=self.storage,
                timeout_segundos=self.settings.download.timeout_segundos,
                max_reintentos=self.settings.download.max_reintentos,
                backoff_base_segundos=self.settings.download.backoff_base_segundos,
                tamano_maximo_bytes=self.settings.download.tamano_maximo_bytes,
            )
        )
        extraccion = DocumentoExtraccionAdapter(
            caso_uso=ExtraerDocumentoUseCase(
                parser_factory=self.parser_factory,
                rule_engine=self.rule_engine,
                persona_repository=persona_repo,
                funcionario_repository=funcionario_repo,
            ),
            storage=self.storage,
        )

        return MonitoreoContinuoService(
            entidad_repository=entidad_repo,
            publicacion_repository=publicacion_repo,
            documento_repository=documento_repo,
            funcionario_repository=funcionario_repo,
            persona_repository=persona_repo,
            descubrimiento=descubrimiento,
            descarga=descarga,
            extraccion=extraccion,
            verificacion_remota=self.verificacion_remota,
            verificacion_service=verificacion_service,
            comparar_documentos=comparar_documentos,
        )

    @staticmethod
    def crear_historial_service(sesion: Session) -> HistorialService:
        """Submodulos 5.2-5.4: consultas de historial de cargo/dependencia."""
        return HistorialService(SqlAlchemyVersionFuncionarioRepository(sesion))

    @staticmethod
    def crear_timeline_service(sesion: Session) -> TimelineService:
        """Submodulo 5.13."""
        return TimelineService(
            verificacion_repository=SqlAlchemyVerificacionRepository(sesion),
            alerta_repository=SqlAlchemyAlertaRepository(sesion),
            auditoria_repository=SqlAlchemyAuditoriaComparacionRepository(sesion),
            documento_repository=SqlAlchemyDocumentoRepository(sesion),
        )

    # -- Modulo 6: Motor de Identidad, Enriquecimiento de Personas y --------
    # -- Fuentes Externas -------------------------------------------------------

    @cached_property
    def rule_engine_identidad(self) -> RuleEngineIdentidad:
        """Motor de Reglas del Modulo 6 (YAML, archivo separado del de
        Modulos 4/5) -- pesos de scoring (6.3), umbrales de fusion (6.21),
        cache por fuente (6.8), priorizacion por cargo (6.11)."""
        return cargar_rule_engine_identidad()

    def crear_resolver_persona_master_use_case(self, sesion: Session) -> ResolverOCrearPersonaMasterUseCase:
        """Submodulos 6.1/6.2/6.21: UNICO punto de entrada para dar de
        alta una PersonaMaster (garantiza "nunca personas duplicadas")."""
        persona_master_repo = SqlAlchemyPersonaMasterRepository(sesion)
        caso_revision_repo = SqlAlchemyCasoRevisionIdentidadRepository(sesion)
        evento_perfil_repo = SqlAlchemyEventoPerfilRepository(sesion)

        identity_resolution_service = IdentityResolutionService(
            persona_master_repo, self.rule_engine_identidad.scoring
        )
        fusion_service = FusionService(
            persona_master_repository=persona_master_repo,
            caso_revision_repository=caso_revision_repo,
            evento_perfil_repository=evento_perfil_repo,
            umbrales=self.rule_engine_identidad.fusion,
        )
        return ResolverOCrearPersonaMasterUseCase(
            persona_master_repository=persona_master_repo,
            identity_resolution_service=identity_resolution_service,
            fusion_service=fusion_service,
        )

    def crear_enriquecer_persona_use_case(self, sesion: Session) -> EnriquecerPersonaUseCase:
        """Submodulo 6.7: pipeline completo de Enriquecimiento (cache por
        fuente -> versionado -> eventos/alertas). Las fuentes concretas
        (SENESCYT, etc.) las provee el LLAMADOR -- este metodo no conoce
        ninguna, solo arma el motor que las va a orquestar."""
        persona_master_repo = SqlAlchemyPersonaMasterRepository(sesion)
        registro_fuente_repo = SqlAlchemyRegistroFuenteRepository(sesion)
        atributo_trazable_repo = SqlAlchemyAtributoTrazableRepository(sesion)
        consulta_fuente_log_repo = SqlAlchemyConsultaFuenteLogRepository(sesion)
        alerta_perfil_repo = SqlAlchemyAlertaPerfilRepository(sesion)
        evento_perfil_repo = SqlAlchemyEventoPerfilRepository(sesion)

        cache_service = CacheFuenteService(consulta_fuente_log_repo, self.rule_engine_identidad.cache_por_fuente)
        registro_fuente_service = RegistroFuenteService(registro_fuente_repo, atributo_trazable_repo)
        auditoria_service = AuditoriaConsultaFuenteService(consulta_fuente_log_repo)
        alerta_perfil_service = AlertaPerfilService(alerta_perfil_repo)
        evento_perfil_service = EventoPerfilService(evento_perfil_repo)

        enriquecimiento_service = EnriquecimientoService(
            cache_service=cache_service,
            registro_fuente_service=registro_fuente_service,
            auditoria_service=auditoria_service,
            alerta_perfil_service=alerta_perfil_service,
            evento_perfil_service=evento_perfil_service,
            persona_master_repository=persona_master_repo,
        )
        return EnriquecerPersonaUseCase(enriquecimiento_service)

    @staticmethod
    def crear_timeline_persona_service(sesion: Session) -> TimelinePersonaService:
        """Submodulo 6.5 -- reutiliza `HistorialService` (Modulo 5) sin
        reimplementar el historial institucional."""
        return TimelinePersonaService(
            historial_service=Container.crear_historial_service(sesion),
            registro_fuente_repository=SqlAlchemyRegistroFuenteRepository(sesion),
        )

    @staticmethod
    def crear_perfil_persona_service(sesion: Session) -> PerfilPersonaService:
        """Submodulos 6.4/6.16: ensambla el contrato oficial `PerfilPersonaDTO`."""
        return PerfilPersonaService(
            persona_master_repository=SqlAlchemyPersonaMasterRepository(sesion),
            registro_fuente_repository=SqlAlchemyRegistroFuenteRepository(sesion),
            historial_service=Container.crear_historial_service(sesion),
            evento_perfil_repository=SqlAlchemyEventoPerfilRepository(sesion),
            alerta_perfil_repository=SqlAlchemyAlertaPerfilRepository(sesion),
            timeline_service=Container.crear_timeline_persona_service(sesion),
        )

    def crear_priorizacion_service(self) -> PriorizacionService:
        """Submodulo 6.11 -- no depende de ninguna sesion (solo config)."""
        return PriorizacionService(self.rule_engine_identidad.priorizacion)

    # -- Modulo 7: Adaptador SENESCYT + Enriquecimiento Academico -----------

    @cached_property
    def rule_engine_academico(self) -> RuleEngineAcademico:
        """Motor de Reglas del Modulo 7 (YAML, archivo separado de los de
        Modulos 4/5/6) -- catalogos de normalizacion (titulos/
        universidades/niveles) y vigencia del cache por persona (7.10)."""
        return cargar_rule_engine_academico()

    @cached_property
    def senescyt_adapter(self) -> SenescytAdapter:
        """`base_url` inyectable por variable de entorno: SENESCYT no
        tiene, al momento de este modulo, una API publica documentada de
        forma estable (Submodulo 7.2: "no asumir aun como responde") --
        se deja explicitamente configurable en vez de hardcodear un
        endpoint que podria no ser el correcto."""
        base_url = os.getenv("SENESCYT_BASE_URL", "https://www.senescyt.gob.ec/consultas")
        return SenescytAdapter(base_url=base_url)

    def crear_enriquecimiento_academico_service(self, sesion: Session) -> EnriquecimientoAcademicoService:
        """Submodulo 7.11: arma el pipeline completo de Enriquecimiento
        Academico ligado a `sesion`."""
        consulta_repo = SqlAlchemyConsultaSenescytRepository(sesion)
        titulo_repo = SqlAlchemyTituloAcademicoRepository(sesion)
        version_repo = SqlAlchemyTituloVersionAcademicaRepository(sesion)
        historial_repo = SqlAlchemyHistorialAcademicoRepository(sesion)
        alerta_repo = SqlAlchemyAlertaAcademicaRepository(sesion)
        evento_repo = SqlAlchemyEventoAcademicoRepository(sesion)

        return EnriquecimientoAcademicoService(
            cache_service=CacheSenescytService(consulta_repo, self.rule_engine_academico.cache),
            senescyt_port=self.senescyt_adapter,
            consulta_service=ConsultaSenescytService(consulta_repo),
            comparacion_service=ComparacionAcademicaService(titulo_repo),
            titulo_service=TituloAcademicoService(titulo_repo, version_repo, historial_repo),
            alerta_service=AlertaAcademicaService(alerta_repo),
            evento_service=EventoAcademicoService(evento_repo),
            rule_engine_academico=self.rule_engine_academico,
        )

    def crear_enriquecer_persona_academica_use_case(self, sesion: Session) -> EnriquecerPersonaAcademicaUseCase:
        """Submodulo 7.11 -- reutiliza `ResolverOCrearPersonaMasterUseCase`
        (Modulo 6) y el Job Manager (Modulo 4), ambos sin modificarlos."""
        return EnriquecerPersonaAcademicaUseCase(
            resolver_persona_master_use_case=self.crear_resolver_persona_master_use_case(sesion),
            enriquecimiento_service=self.crear_enriquecimiento_academico_service(sesion),
            job_manager=JobManagerService(SqlAlchemyJobRepository(sesion)),
        )

    def crear_enriquecer_masivo_academico_use_case(self, sesion: Session) -> EnriquecerMasivoAcademicoUseCase:
        """Submodulo 7.12."""
        return EnriquecerMasivoAcademicoUseCase(
            persona_master_repository=SqlAlchemyPersonaMasterRepository(sesion),
            enriquecimiento_service=self.crear_enriquecimiento_academico_service(sesion),
            job_manager=JobManagerService(SqlAlchemyJobRepository(sesion)),
        )

    @staticmethod
    def crear_perfil_academico_service(sesion: Session) -> PerfilAcademicoService:
        """Submodulo 7.16: ensambla el contrato oficial `PerfilAcademicoDTO`."""
        return PerfilAcademicoService(
            persona_master_repository=SqlAlchemyPersonaMasterRepository(sesion),
            titulo_repository=SqlAlchemyTituloAcademicoRepository(sesion),
            historial_repository=SqlAlchemyHistorialAcademicoRepository(sesion),
            evento_repository=SqlAlchemyEventoAcademicoRepository(sesion),
            alerta_repository=SqlAlchemyAlertaAcademicaRepository(sesion),
        )

    @staticmethod
    def crear_metricas_academicas_service(sesion: Session) -> MetricasAcademicasService:
        """Submodulo 7.18."""
        return MetricasAcademicasService(
            consulta_repository=SqlAlchemyConsultaSenescytRepository(sesion),
            historial_repository=SqlAlchemyHistorialAcademicoRepository(sesion),
        )

    def crear_programador_enriquecimiento_service(self, sesion: Session) -> ProgramadorEnriquecimientoService:
        """Submodulo 7.20, mejora 2 -- reutiliza `PriorizacionService`
        (Modulo 6) sin modificarlo."""
        return ProgramadorEnriquecimientoService(
            persona_master_repository=SqlAlchemyPersonaMasterRepository(sesion),
            consulta_repository=SqlAlchemyConsultaSenescytRepository(sesion),
            alerta_repository=SqlAlchemyAlertaAcademicaRepository(sesion),
            priorizacion_service=self.crear_priorizacion_service(),
            reglas_cache=self.rule_engine_academico.cache,
        )

    # -- Modulo 8: Motor de Consulta al Foro de Abogados, Fusion de Datos --
    # -- y Perfil Consolidado del Funcionario --------------------------------

    @cached_property
    def rule_engine_foro(self) -> RuleEngineForo:
        """Motor de Reglas del Modulo 8 (YAML, archivo separado de los de
        Modulos 4/5/6/7) -- catalogo de campos (8.3), cache por persona
        (8.8) y Circuit Breaker (8.9)."""
        return cargar_rule_engine_foro()

    @cached_property
    def foro_abogados_adapter(self) -> ForoAbogadosAdapter:
        """`base_url` inyectable por variable de entorno: el Foro de
        Abogados no tiene, al momento de este modulo, una API publica
        documentada de forma estable (Submodulo 8.2: "no asumir aun como
        responde") -- se deja explicitamente configurable en vez de
        hardcodear un endpoint que podria no ser el correcto."""
        base_url = os.getenv("FORO_ABOGADOS_BASE_URL", "https://www.foroabogados.gob.ec/consultas")
        return ForoAbogadosAdapter(
            base_url=base_url, catalogo_campos=self.rule_engine_foro.campos,
            reglas_circuito=self.rule_engine_foro.circuito,
        )

    def crear_enriquecimiento_foro_service(self, sesion: Session) -> EnriquecimientoForoService:
        """Submodulo 8.12: arma el pipeline completo de consulta al Foro
        ligado a `sesion`."""
        consulta_repo = SqlAlchemyConsultaForoRepository(sesion)
        registro_repo = SqlAlchemyRegistroForoRepository(sesion)
        version_repo = SqlAlchemyRegistroForoVersionRepository(sesion)
        historial_repo = SqlAlchemyHistorialForoRepository(sesion)
        alerta_repo = SqlAlchemyAlertaForoRepository(sesion)
        evento_repo = SqlAlchemyEventoForoRepository(sesion)

        return EnriquecimientoForoService(
            cache_service=CacheForoService(consulta_repo, self.rule_engine_foro.cache),
            foro_port=self.foro_abogados_adapter,
            consulta_service=ConsultaForoService(consulta_repo),
            comparacion_service=ComparacionForoService(registro_repo),
            registro_service=RegistroForoService(registro_repo, version_repo, historial_repo),
            alerta_service=AlertaForoService(alerta_repo),
            evento_service=EventoForoService(evento_repo),
            rule_engine_foro=self.rule_engine_foro,
        )

    def crear_perfil_consolidado_service(self, sesion: Session) -> PerfilConsolidadoService:
        """Submodulo 8.10 -- ensambla `{"persona": {}, "transparencia":
        {}, "senescyt": {}, "foro": {}}` reutilizando `PerfilAcademicoService`
        (Modulo 7) sin modificarlo."""
        return PerfilConsolidadoService(
            persona_master_repository=SqlAlchemyPersonaMasterRepository(sesion),
            persona_repository=SqlAlchemyPersonaRepository(sesion),
            funcionario_repository=SqlAlchemyFuncionarioRepository(sesion),
            entidad_repository=SqlAlchemyEntidadRepository(sesion),
            perfil_academico_service=Container.crear_perfil_academico_service(sesion),
            registro_foro_repository=SqlAlchemyRegistroForoRepository(sesion),
            historial_foro_repository=SqlAlchemyHistorialForoRepository(sesion),
            evento_foro_repository=SqlAlchemyEventoForoRepository(sesion),
            alerta_foro_repository=SqlAlchemyAlertaForoRepository(sesion),
        )

    @staticmethod
    def crear_metricas_foro_service(sesion: Session) -> MetricasForoService:
        """Submodulo 8.15."""
        return MetricasForoService(consulta_repository=SqlAlchemyConsultaForoRepository(sesion))

    def crear_consultar_persona_foro_use_case(self, sesion: Session) -> ConsultarPersonaForoUseCase:
        """Submodulo 8.12 (`consultar_persona()`) -- reutiliza
        `ResolverOCrearPersonaMasterUseCase` (Modulo 6),
        `EnriquecimientoAcademicoService` (Modulo 7) y el Job Manager
        (Modulo 4), todos sin modificarlos."""
        return ConsultarPersonaForoUseCase(
            resolver_persona_master_use_case=self.crear_resolver_persona_master_use_case(sesion),
            enriquecimiento_academico_service=self.crear_enriquecimiento_academico_service(sesion),
            enriquecimiento_foro_service=self.crear_enriquecimiento_foro_service(sesion),
            perfil_academico_service=Container.crear_perfil_academico_service(sesion),
            perfil_consolidado_service=self.crear_perfil_consolidado_service(sesion),
            job_manager=JobManagerService(SqlAlchemyJobRepository(sesion)),
        )

    def crear_consultar_por_cedula_foro_use_case(self, sesion: Session) -> ConsultarPorCedulaForoUseCase:
        """Submodulo 8.12 (`consultar_por_cedula()`)."""
        return ConsultarPorCedulaForoUseCase(
            persona_repository=SqlAlchemyPersonaRepository(sesion),
            consultar_persona_use_case=self.crear_consultar_persona_foro_use_case(sesion),
        )

    def crear_consultar_masivo_foro_use_case(self, sesion: Session) -> ConsultarMasivoForoUseCase:
        """Submodulo 8.13 -- "debe reutilizar exactamente el mismo
        pipeline" (8.12): mismo `EnriquecimientoForoService`."""
        return ConsultarMasivoForoUseCase(
            persona_master_repository=SqlAlchemyPersonaMasterRepository(sesion),
            persona_repository=SqlAlchemyPersonaRepository(sesion),
            enriquecimiento_foro_service=self.crear_enriquecimiento_foro_service(sesion),
            job_manager=JobManagerService(SqlAlchemyJobRepository(sesion)),
        )

    def crear_consultar_entidad_use_case(self, sesion: Session) -> ConsultarEntidadUseCase:
        """EL FLUJO OBLIGATORIO completo del Modulo 8 (Submodulo 8.11):
        Portal Transparencia -> Extraer funcionarios -> Filtrar area
        juridica -> SENESCYT -> Obtener Cedula -> Foro de Abogados ->
        Extraer informacion profesional -> Fusionar -> Guardar historial
        -> Mostrar resultado."""
        return ConsultarEntidadUseCase(
            entidad_repository=SqlAlchemyEntidadRepository(sesion),
            funcionario_repository=SqlAlchemyFuncionarioRepository(sesion),
            persona_repository=SqlAlchemyPersonaRepository(sesion),
            registro_foro_repository=SqlAlchemyRegistroForoRepository(sesion),
            resolver_persona_master_use_case=self.crear_resolver_persona_master_use_case(sesion),
            enriquecimiento_academico_service=self.crear_enriquecimiento_academico_service(sesion),
            enriquecimiento_foro_service=self.crear_enriquecimiento_foro_service(sesion),
            job_manager=JobManagerService(SqlAlchemyJobRepository(sesion)),
        )

    # -- Modulo 9: Orquestador Maestro del Sistema GovData -------------------

    @cached_property
    def rule_engine_orquestador(self) -> RuleEngineOrquestador:
        """Motor de Reglas del Modulo 9 (YAML, archivo separado de todos
        los anteriores) -- pesos del Motor de Prioridades (9.5), catalogo
        de Politicas de Ejecucion (mejora del cliente) y comportamiento
        general de la cola (9.6/9.7/9.8/9.13)."""
        return cargar_rule_engine_orquestador()

    def _reglas_cache_senescyt_para_politica(self, politica: PoliticaEjecucion) -> ReglasCacheSenescyt:
        """Truco documentado en `GovDataPipelineOrchestrator`: una
        politica con `forzar_actualizacion=True` (ej. "Actualizacion
        Completa") construye `EnriquecimientoAcademicoService` (Modulo 7,
        NUNCA modificado) con una vigencia de cache de 0 dias --
        `debe_consultar()` da `True` siempre, sin tocar una linea de
        Modulo 7."""
        if politica.forzar_actualizacion:
            return ReglasCacheSenescyt(dias_vigencia=0)
        return self.rule_engine_academico.cache

    def _reglas_cache_foro_para_politica(self, politica: PoliticaEjecucion) -> ReglasCacheForo:
        if politica.forzar_actualizacion:
            return ReglasCacheForo(dias_vigencia=0)
        return self.rule_engine_foro.cache

    def crear_enriquecimiento_academico_service_con_politica(
        self, sesion: Session, politica: PoliticaEjecucion
    ) -> EnriquecimientoAcademicoService:
        """Igual que `crear_enriquecimiento_academico_service` (Submodulo
        7.11), pero con el cache ajustado segun la `PoliticaEjecucion`
        activa (Motor de Politicas, Submodulo 9.13)."""
        consulta_repo = SqlAlchemyConsultaSenescytRepository(sesion)
        titulo_repo = SqlAlchemyTituloAcademicoRepository(sesion)
        version_repo = SqlAlchemyTituloVersionAcademicaRepository(sesion)
        historial_repo = SqlAlchemyHistorialAcademicoRepository(sesion)
        alerta_repo = SqlAlchemyAlertaAcademicaRepository(sesion)
        evento_repo = SqlAlchemyEventoAcademicoRepository(sesion)

        return EnriquecimientoAcademicoService(
            cache_service=CacheSenescytService(consulta_repo, self._reglas_cache_senescyt_para_politica(politica)),
            senescyt_port=self.senescyt_adapter,
            consulta_service=ConsultaSenescytService(consulta_repo),
            comparacion_service=ComparacionAcademicaService(titulo_repo),
            titulo_service=TituloAcademicoService(titulo_repo, version_repo, historial_repo),
            alerta_service=AlertaAcademicaService(alerta_repo),
            evento_service=EventoAcademicoService(evento_repo),
            rule_engine_academico=self.rule_engine_academico,
        )

    def crear_enriquecimiento_foro_service_con_politica(
        self, sesion: Session, politica: PoliticaEjecucion
    ) -> EnriquecimientoForoService:
        """Igual que `crear_enriquecimiento_foro_service` (Submodulo
        8.12), pero con el cache ajustado segun la `PoliticaEjecucion`
        activa."""
        consulta_repo = SqlAlchemyConsultaForoRepository(sesion)
        registro_repo = SqlAlchemyRegistroForoRepository(sesion)
        version_repo = SqlAlchemyRegistroForoVersionRepository(sesion)
        historial_repo = SqlAlchemyHistorialForoRepository(sesion)
        alerta_repo = SqlAlchemyAlertaForoRepository(sesion)
        evento_repo = SqlAlchemyEventoForoRepository(sesion)

        return EnriquecimientoForoService(
            cache_service=CacheForoService(consulta_repo, self._reglas_cache_foro_para_politica(politica)),
            foro_port=self.foro_abogados_adapter,
            consulta_service=ConsultaForoService(consulta_repo),
            comparacion_service=ComparacionForoService(registro_repo),
            registro_service=RegistroForoService(registro_repo, version_repo, historial_repo),
            alerta_service=AlertaForoService(alerta_repo),
            evento_service=EventoForoService(evento_repo),
            rule_engine_foro=self.rule_engine_foro,
        )

    def crear_govdata_pipeline_orchestrator(self, sesion: Session) -> GovDataPipelineOrchestrator:
        """Submodulo 9.1: EL UNICO PUNTO DE ENTRADA del sistema. Reutiliza
        `MonitoreoContinuoService` (Modulo 5), `ResolverOCrearPersonaMasterUseCase`
        (Modulo 6) y `PerfilConsolidadoService` (Modulo 8), todos sin
        modificarlos."""
        motor_politicas = MotorPoliticasService(self.rule_engine_orquestador.politicas)
        cola = ColaTrabajosOrquestadorService(SqlAlchemyTrabajoOrquestadorRepository(sesion))
        auditoria = AuditoriaOrquestacionService(SqlAlchemyAuditoriaEtapaRepository(sesion))

        return GovDataPipelineOrchestrator(
            entidad_repository=SqlAlchemyEntidadRepository(sesion),
            funcionario_repository=SqlAlchemyFuncionarioRepository(sesion),
            persona_repository=SqlAlchemyPersonaRepository(sesion),
            monitoreo_service=self.crear_monitoreo_service(sesion),
            resolver_persona_master_use_case=self.crear_resolver_persona_master_use_case(sesion),
            perfil_consolidado_service=self.crear_perfil_consolidado_service(sesion),
            crear_enriquecimiento_academico=lambda politica: self.crear_enriquecimiento_academico_service_con_politica(sesion, politica),
            crear_enriquecimiento_foro=lambda politica: self.crear_enriquecimiento_foro_service_con_politica(sesion, politica),
            motor_politicas=motor_politicas,
            cola=cola,
            auditoria=auditoria,
            politica_defecto=self.rule_engine_orquestador.cola.politica_defecto,
            ejecutor_aislado=self._ejecutar_entidad_en_sesion_aislada,
        )

    def _ejecutar_entidad_en_sesion_aislada(
        self, nombre_entidad: str, tipo_trabajo: TipoTrabajoOrquestador, nombre_politica: str,
    ) -> ResultadoOrquestacionDTO:
        """Callback inyectado como `ejecutor_aislado` (Submodulos
        9.5/9.6/9.8): CADA llamada abre y confirma (o revierte) su PROPIA
        `Session` -- es lo que permite que `consultar_masivo`/
        `actualizar_masivo` procesen entidades en paralelo sin que el
        fallo de una arrastre el trabajo ya confirmado de las demas."""
        with self.nueva_sesion() as sesion:
            orquestador = self.crear_govdata_pipeline_orchestrator(sesion)
            if tipo_trabajo in (TipoTrabajoOrquestador.ACTUALIZACION_ENTIDAD, TipoTrabajoOrquestador.ACTUALIZACION_MASIVA):
                return orquestador.actualizar_entidad(nombre_entidad)
            return orquestador.consultar_entidad(nombre_entidad, nombre_politica)

    def reanudar_trabajos_interrumpidos(self) -> int:
        """Submodulo 9.7 (Reanudacion automatica): se llama UNA vez al
        arrancar el proceso (ver `scripts/orquestador.py`) -- cualquier
        `TrabajoOrquestador` que quedo en EJECUTANDO por una caida previa
        del servidor se reencola automaticamente."""
        with self.nueva_sesion() as sesion:
            cola = ColaTrabajosOrquestadorService(SqlAlchemyTrabajoOrquestadorRepository(sesion))
            return cola.reanudar_interrumpidos()

    @staticmethod
    def crear_dashboard_interno_service(sesion: Session) -> DashboardInternoService:
        """Submodulo 9.11 (Dashboard interno, solo backend)."""
        return DashboardInternoService(SqlAlchemyTrabajoOrquestadorRepository(sesion))

    @staticmethod
    def crear_motor_estadisticas_service(sesion: Session) -> MotorEstadisticasService:
        """Submodulo 9.12 (Motor de Estadisticas)."""
        return MotorEstadisticasService(SqlAlchemyAuditoriaEtapaRepository(sesion))

    # -- Modulo 10: API REST -- capa de acceso, NUNCA reimplementa el -------
    # -- motor (Modulos 1-9 congelados). Wiring aditivo: unicamente NUEVOS --
    # -- casos de uso/puertos/adaptadores propios de este modulo. -----------

    @staticmethod
    def crear_listar_entidades_api_use_case(sesion: Session) -> ListarEntidadesApiUseCase:
        return ListarEntidadesApiUseCase(
            entidad_repository=SqlAlchemyEntidadRepository(sesion),
            publicacion_repository=SqlAlchemyPublicacionRepository(sesion),
        )

    @staticmethod
    def crear_funcionario_consulta_paginada_repository(
        sesion: Session,
    ) -> SqlAlchemyFuncionarioConsultaPaginadaRepository:
        """Submodulo 10.33 (rendimiento): puerto NUEVO, propio del Modulo
        10 -- ver docstring de `FuncionarioConsultaPaginadaPort`."""
        return SqlAlchemyFuncionarioConsultaPaginadaRepository(sesion)

    @staticmethod
    def crear_obtener_alertas_funcionario_use_case(sesion: Session) -> ObtenerAlertasFuncionarioUseCase:
        return ObtenerAlertasFuncionarioUseCase(
            alerta_perfil_repository=SqlAlchemyAlertaPerfilRepository(sesion),
            alerta_academica_repository=SqlAlchemyAlertaAcademicaRepository(sesion),
            alerta_foro_repository=SqlAlchemyAlertaForoRepository(sesion),
        )

    @staticmethod
    def crear_obtener_cambios_entidad_use_case(sesion: Session) -> ObtenerCambiosEntidadUseCase:
        return ObtenerCambiosEntidadUseCase(historial_service=Container.crear_historial_service(sesion))
