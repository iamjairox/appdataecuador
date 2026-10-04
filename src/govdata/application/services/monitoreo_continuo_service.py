"""Servicio: MonitoreoContinuoService -- Submodulo 5.15 (NUEVO,
obligatorio): Motor de Monitoreo Continuo.

Implementa EXACTAMENTE el flujo obligatorio del cliente:

    Entidad -> Consultar ultima publicacion -> ¿Documento nuevo?
        NO  -> Finalizar
        SI  -> Comparar hash -> ¿Hash igual?
            SI -> No descargar -> Registrar verificacion -> Finalizar
            NO -> Descargar -> Extraer -> Comparar contra version
                  anterior -> Generar diferencias -> Actualizar
                  historial -> Crear alertas -> Persistir -> Mostrar resultado

"Nunca descargar un documento si el hash no cambio" se resuelve en DOS
capas (ver `VerificacionRemotaPort`): un chequeo LIVIANO (HTTP HEAD,
ETag/Last-Modified) ANTES de descargar, y el hash SHA256 real (autoridad
final, Modulo 3) inmediatamente DESPUES de descargar -- si de todas
formas coincide con el ya conocido (el HEAD pudo dar un falso positivo),
tampoco se vuelve a extraer/comparar. "Nunca reprocesar un documento ya
procesado" se resuelve verificando si YA existe una `Verificacion`
registrada para el `documento_id` exacto que devolvio el descubrimiento.
"""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.resultado_monitoreo_dto import ResultadoMonitoreoDTO
from govdata.application.dto.resultado_unificado_dto import FuncionarioUnificadoDTO
from govdata.application.dto.verificacion_dto import VerificacionDTO
from govdata.application.ports.descarga_port import DescargaPort
from govdata.application.ports.descubrimiento_port import DescubrimientoPort
from govdata.application.ports.documento_repository_port import DocumentoRepositoryPort
from govdata.application.ports.entidad_repository_port import EntidadRepositoryPort
from govdata.application.ports.extraccion_port import ExtraccionPort
from govdata.application.ports.funcionario_repository_port import FuncionarioRepositoryPort
from govdata.application.ports.persona_repository_port import PersonaRepositoryPort
from govdata.application.ports.publicacion_repository_port import PublicacionRepositoryPort
from govdata.application.ports.verificacion_remota_port import VerificacionRemotaPort
from govdata.application.services.verificacion_service import VerificacionService
from govdata.application.use_cases.comparar_documentos_use_case import CompararDocumentosUseCase
from govdata.config.logging_config import get_logger
from govdata.domain.entities.entidad import Entidad
from govdata.domain.exceptions.domain_exceptions import GovDataError
from govdata.domain.rules.convertir_funcionario_unificado import funcionario_a_unificado

logger = get_logger(__name__)


class MonitoreoContinuoService:
    def __init__(
        self,
        entidad_repository: EntidadRepositoryPort,
        publicacion_repository: PublicacionRepositoryPort,
        documento_repository: DocumentoRepositoryPort,
        funcionario_repository: FuncionarioRepositoryPort,
        persona_repository: PersonaRepositoryPort,
        descubrimiento: DescubrimientoPort,
        descarga: DescargaPort,
        extraccion: ExtraccionPort,
        verificacion_remota: VerificacionRemotaPort,
        verificacion_service: VerificacionService,
        comparar_documentos: CompararDocumentosUseCase,
    ) -> None:
        self._entidad_repository = entidad_repository
        self._publicacion_repository = publicacion_repository
        self._documento_repository = documento_repository
        self._funcionario_repository = funcionario_repository
        self._persona_repository = persona_repository
        self._descubrimiento = descubrimiento
        self._descarga = descarga
        self._extraccion = extraccion
        self._verificacion_remota = verificacion_remota
        self._verificacion_service = verificacion_service
        self._comparar_documentos = comparar_documentos

    def cerrar(self) -> None:
        """Libera los recursos del adaptador de descubrimiento (FASE 3.8
        -- p. ej. el navegador Playwright de `DpeDescubrimientoAdapter`).
        El llamador debe invocar esto tras cada `monitorear()` -- esta
        instancia vive por peticion/trabajo, nunca se reutiliza."""
        self._descubrimiento.cerrar()

    def monitorear(self, entidad: Entidad) -> ResultadoMonitoreoDTO:
        if entidad.id is None:
            raise GovDataError("Entidad requiere id para monitorear")

        ahora = datetime.now(UTC)
        resultado_descubrimiento = self._descubrimiento.descubrir(entidad)

        if (
            not resultado_descubrimiento.exito
            or resultado_descubrimiento.publicacion is None
            or resultado_descubrimiento.documento is None
        ):
            return self._sin_cambio(entidad.id, "sin_publicacion_o_documento", ahora)

        publicacion_actual = resultado_descubrimiento.publicacion
        documento_descubierto = resultado_descubrimiento.documento

        if self._ya_fue_verificado(entidad.id, documento_descubierto.id):
            return self._sin_cambio(entidad.id, "documento_ya_procesado", ahora, documento_descubierto.id)

        publicacion_anterior = self._publicacion_repository.buscar_ultima_por_entidad(
            entidad.id, excluir_mes=publicacion_actual.mes_publicado
        )
        documento_anterior = (
            self._documento_repository.buscar_por_publicacion(publicacion_anterior.id)
            if publicacion_anterior is not None and publicacion_anterior.id is not None
            else None
        )

        if documento_anterior is not None and documento_anterior.esta_descargado:
            hay_cambios_remoto = self._verificacion_remota.hay_cambios(
                documento_descubierto.url_documento, documento_anterior.etag, documento_anterior.last_modified
            )
            if not hay_cambios_remoto:
                return self._sin_cambio(
                    entidad.id, "hash_remoto_sin_cambios", ahora, documento_anterior.id, documento_anterior.hash_sha256
                )

        # El descubrimiento puede devolver el mismo documento que otra
        # consulta ya descargó. Reutilizarlo evita reclamar de nuevo una
        # fila en estado DESCARGADO (que antes se reportaba erróneamente
        # como "reclamada por otro worker") y permite continuar con la
        # extracción pendiente para cualquier entidad.
        if documento_descubierto.esta_descargado and documento_descubierto.ruta_almacenamiento:
            documento_descargado = documento_descubierto
            logger.info("documento_descargado_reutilizado", documento_id=documento_descargado.id)
        else:
            documento_descargado = self._descarga.descargar(documento_descubierto)

        if documento_anterior is not None and documento_anterior.hash_sha256 == documento_descargado.hash_sha256:
            return self._sin_cambio(
                entidad.id, "hash_identico_tras_descarga", ahora, documento_descargado.id, documento_descargado.hash_sha256
            )

        resultado_extraccion = self._extraccion.extraer(entidad, documento_descargado, publicacion_actual.mes_publicado)

        funcionarios_anteriores = (
            self._funcionarios_unificados_vigentes(entidad.id) if documento_anterior is not None else []
        )

        resultado_comparacion = self._comparar_documentos.ejecutar(
            entidad=entidad,
            documento_anterior=documento_anterior,
            documento_actual=documento_descargado,
            funcionarios_anteriores=funcionarios_anteriores,
            funcionarios_actuales=resultado_extraccion.funcionarios,
            mes_publicado_actual=publicacion_actual.mes_publicado,
            mes_publicado_anterior=publicacion_anterior.mes_publicado if publicacion_anterior else None,
            fecha_comparacion=ahora.date(),
        )

        verificacion = self._verificacion_service.registrar(
            entidad_id=entidad.id,
            hubo_cambio=True,
            motivo="cambios_detectados",
            verificado_en=ahora,
            documento_id=documento_descargado.id,
            hash_verificado=documento_descargado.hash_sha256,
        )
        logger.info("monitoreo_completado", entidad_id=entidad.id, hubo_cambio=True)
        return ResultadoMonitoreoDTO(
            entidad_id=entidad.id,
            hubo_cambio=True,
            verificacion=VerificacionDTO.desde_entidad(verificacion),
            comparacion=resultado_comparacion,
        )

    def monitorear_masiva(self, entidades: list[Entidad] | None = None) -> list[ResultadoMonitoreoDTO]:
        """Reutiliza `monitorear` por cada entidad -- ningun pipeline
        duplicado (mismo patron que `ConsultaService.consultar_masiva`,
        Modulo 4). Un fallo individual nunca detiene el lote."""
        objetivo = entidades if entidades is not None else self._entidad_repository.listar_activas()
        resultados: list[ResultadoMonitoreoDTO] = []
        for entidad in objetivo:
            try:
                resultados.append(self.monitorear(entidad))
            except GovDataError as exc:
                logger.warning("monitoreo_entidad_fallido", entidad=entidad.nombre, error=str(exc))
                continue
        logger.info("monitoreo_masivo_finalizado", total=len(objetivo), procesadas=len(resultados))
        return resultados

    # -- Helpers ---------------------------------------------------------------

    def _ya_fue_verificado(self, entidad_id: int, documento_id: int | None) -> bool:
        if documento_id is None:
            return False
        ultima = self._verificacion_service.ultima_verificacion(entidad_id)
        return ultima is not None and ultima.documento_id == documento_id

    def _sin_cambio(
        self,
        entidad_id: int,
        motivo: str,
        verificado_en: datetime,
        documento_id: int | None = None,
        hash_verificado: str | None = None,
    ) -> ResultadoMonitoreoDTO:
        verificacion = self._verificacion_service.registrar(
            entidad_id=entidad_id,
            hubo_cambio=False,
            motivo=motivo,
            verificado_en=verificado_en,
            documento_id=documento_id,
            hash_verificado=hash_verificado,
        )
        logger.info("monitoreo_completado", entidad_id=entidad_id, hubo_cambio=False, motivo=motivo)
        return ResultadoMonitoreoDTO(
            entidad_id=entidad_id, hubo_cambio=False, verificacion=VerificacionDTO.desde_entidad(verificacion)
        )

    def _funcionarios_unificados_vigentes(self, entidad_id: int) -> list[FuncionarioUnificadoDTO]:
        """El snapshot "anterior" para comparar es SIEMPRE lo que hoy esta
        vigente para la entidad -- NUNCA lo que quedo asociado al
        `documento_id` exacto de la publicacion previa. Si esa publicacion
        no trajo cambios reales, `PersistenciaInteligenteService` la
        ignora (Submodulo 5.11: "nunca insertar duplicados") y por lo
        tanto NUNCA re-etiqueta los `Funcionario` existentes con ese
        `documento_id` -- filtrar por documento ahi perderia silenciosamente
        el snapshot completo (el caso mas comun en monitoreo real: la
        mayoria de los meses no traen cambios)."""
        funcionarios = self._funcionario_repository.listar_por_entidad(entidad_id, solo_vigentes=True)
        resultado: list[FuncionarioUnificadoDTO] = []
        for funcionario in funcionarios:
            persona = self._persona_repository.buscar_por_id(funcionario.persona_id)
            if persona is None:
                continue
            resultado.append(funcionario_a_unificado(funcionario, persona))
        return resultado
