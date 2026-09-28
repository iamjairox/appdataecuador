"""Caso de uso: CompararDocumentosUseCase -- Submodulo 5.1 orquestado.

Punto de entrada UNICO para comparar dos versiones (anterior/actual) de
los funcionarios de una entidad. Orquesta, en orden:

    Motor de Comparacion (5.1) -> Criticidad -> Estadisticas (5.12)
        -> Persistencia Inteligente (5.11, que a su vez abre/cierra
           VersionFuncionario via HistorialService 5.2-5.4)
        -> Alertas (5.6) -> Oportunidades Comerciales (5.17)
        -> Eventos (5.7, en PENDIENTE)
        -> Auditoria (5.9)

y produce exactamente el contrato oficial `ResultadoComparacionDTO`
(Submodulo 5.14). Usado tanto por `MonitoreoContinuoService` (5.15) como
por cualquier llamada directa (ej. recomparar un par de documentos ya
descargados, sin pasar por descubrimiento/descarga)."""

from __future__ import annotations

import time
from datetime import UTC, date, datetime

from govdata.application.dto.alerta_dto import AlertaDTO
from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.application.dto.estadisticas_comparacion_dto import EstadisticasComparacionDTO
from govdata.application.dto.resultado_comparacion_dto import ResultadoComparacionDTO
from govdata.application.dto.resultado_unificado_dto import (
    DocumentoResumenDTO,
    EntidadResumenDTO,
    FuncionarioUnificadoDTO,
)
from govdata.application.services.alerta_service import AlertaService
from govdata.application.services.auditoria_comparacion_service import AuditoriaComparacionService
from govdata.application.services.evento_service import EventoService
from govdata.application.services.oportunidad_comercial_service import OportunidadComercialService
from govdata.application.services.persistencia_inteligente_service import (
    PersistenciaInteligenteService,
)
from govdata.config.logging_config import get_logger
from govdata.domain.entities.alerta import Alerta
from govdata.domain.entities.documento import DocumentoTransparencia
from govdata.domain.entities.entidad import Entidad
from govdata.domain.exceptions.domain_exceptions import ComparacionFallidaError, GovDataError
from govdata.domain.rules.clasificador_criticidad import enriquecer_con_criticidad
from govdata.domain.rules.motor_comparacion import calcular_estadisticas, comparar_funcionarios
from govdata.domain.rules.reglas_configurables import RuleEngine
from govdata.domain.value_objects.tipo_cambio import TipoCambio

logger = get_logger(__name__)

_TIPOS_CAMBIO_CAMPO = frozenset(
    {
        TipoCambio.CAMBIO_CARGO,
        TipoCambio.CAMBIO_DEPENDENCIA,
        TipoCambio.CAMBIO_CORREO,
        TipoCambio.CAMBIO_TELEFONO,
        TipoCambio.CAMBIO_AREA,
        TipoCambio.CAMBIO_NOMBRE,
        TipoCambio.CAMBIO_APELLIDO,
        TipoCambio.CAMBIO_MULTIPLE,
    }
)


class CompararDocumentosUseCase:
    def __init__(
        self,
        persistencia_service: PersistenciaInteligenteService,
        alerta_service: AlertaService,
        oportunidad_service: OportunidadComercialService,
        evento_service: EventoService,
        auditoria_service: AuditoriaComparacionService,
        rule_engine: RuleEngine,
    ) -> None:
        self._persistencia_service = persistencia_service
        self._alerta_service = alerta_service
        self._oportunidad_service = oportunidad_service
        self._evento_service = evento_service
        self._auditoria_service = auditoria_service
        self._rule_engine = rule_engine

    def ejecutar(
        self,
        entidad: Entidad,
        documento_anterior: DocumentoTransparencia | None,
        documento_actual: DocumentoTransparencia,
        funcionarios_anteriores: list[FuncionarioUnificadoDTO],
        funcionarios_actuales: list[FuncionarioUnificadoDTO],
        mes_publicado_actual: date,
        mes_publicado_anterior: date | None = None,
        fecha_comparacion: date | None = None,
        ejecutado_por: str = "sistema",
    ) -> ResultadoComparacionDTO:
        if entidad.id is None or documento_actual.id is None:
            raise ComparacionFallidaError("Entidad y Documento actual requieren id para comparar")

        fecha_comparacion = fecha_comparacion or datetime.now(UTC).date()
        auditoria = self._auditoria_service.iniciar(
            entidad.id, documento_actual.id, documento_actual.version, ejecutado_por
        )

        try:
            inicio = time.perf_counter()
            diferencias = comparar_funcionarios(funcionarios_anteriores, funcionarios_actuales)
            diferencias = enriquecer_con_criticidad(diferencias, self._rule_engine.criticidad)
            duracion = time.perf_counter() - inicio

            estadisticas = calcular_estadisticas(
                diferencias, len(funcionarios_anteriores), len(funcionarios_actuales), duracion
            )

            resumen_persistencia = self._persistencia_service.aplicar(
                diferencias, entidad.id, documento_actual.id, fecha_comparacion
            )

            ahora = datetime.now(UTC)
            alertas = self._alerta_service.generar_y_guardar(
                diferencias, estadisticas, entidad.id, documento_actual.id,
                resumen_persistencia.persona_id_por_fingerprint, ahora,
            )
            oportunidades = self._oportunidad_service.generar_y_guardar(
                diferencias, estadisticas, entidad.id, resumen_persistencia.persona_id_por_fingerprint, ahora
            )
            self._evento_service.crear_desde_alertas(alertas, ahora)
            self._evento_service.crear_desde_oportunidades(oportunidades, ahora)

            resultado = self._construir_resultado(
                entidad, documento_anterior, documento_actual, mes_publicado_actual, mes_publicado_anterior,
                diferencias, estadisticas, alertas, ahora,
            )

            cambios_detectados = len(resultado.nuevos) + len(resultado.eliminados) + len(resultado.cambios)
            self._auditoria_service.finalizar(auditoria, cambios_detectados)
            logger.info(
                "comparacion_completada",
                entidad_id=entidad.id,
                documento_id=documento_actual.id,
                nuevos=len(resultado.nuevos),
                eliminados=len(resultado.eliminados),
                cambios=len(resultado.cambios),
                sin_cambios=len(resultado.sin_cambios),
                alertas=len(alertas),
                oportunidades=len(oportunidades),
                duracion_segundos=round(duracion, 3),
            )
            return resultado
        except GovDataError as exc:
            self._auditoria_service.marcar_error(auditoria, str(exc))
            raise ComparacionFallidaError(f"Fallo la comparacion para entidad {entidad.id}: {exc}") from exc

    @staticmethod
    def _construir_resultado(
        entidad: Entidad,
        documento_anterior: DocumentoTransparencia | None,
        documento_actual: DocumentoTransparencia,
        mes_publicado_actual: date,
        mes_publicado_anterior: date | None,
        diferencias: list[DiferenciaFuncionarioDTO],
        estadisticas: EstadisticasComparacionDTO,
        alertas: list[Alerta],
        generado_en: datetime,
    ) -> ResultadoComparacionDTO:
        nuevos = [d for d in diferencias if d.tipo_cambio == TipoCambio.FUNCIONARIO_NUEVO]
        eliminados = [d for d in diferencias if d.tipo_cambio == TipoCambio.FUNCIONARIO_ELIMINADO]
        sin_cambios = [d for d in diferencias if d.tipo_cambio == TipoCambio.SIN_CAMBIOS]
        cambios = [d for d in diferencias if d.tipo_cambio in _TIPOS_CAMBIO_CAMPO]

        return ResultadoComparacionDTO(
            entidad=EntidadResumenDTO(
                id=entidad.id,  # type: ignore[arg-type]
                nombre=entidad.nombre,
                portal_origen=entidad.portal_origen,
                identificador_portal=entidad.metadata_extra.get("identificador_portal"),
            ),
            documento_anterior=(
                DocumentoResumenDTO(
                    id=documento_anterior.id,  # type: ignore[arg-type]
                    tipo_archivo=documento_anterior.tipo_archivo.value,
                    mes_publicado=mes_publicado_anterior,  # type: ignore[arg-type]
                    hash_sha256=documento_anterior.hash_sha256 or "",
                    version=documento_anterior.version,
                    url=documento_anterior.url_documento,
                )
                if documento_anterior is not None
                else None
            ),
            documento_actual=DocumentoResumenDTO(
                id=documento_actual.id,  # type: ignore[arg-type]
                tipo_archivo=documento_actual.tipo_archivo.value,
                mes_publicado=mes_publicado_actual,
                hash_sha256=documento_actual.hash_sha256 or "",
                version=documento_actual.version,
                url=documento_actual.url_documento,
            ),
            nuevos=nuevos,
            eliminados=eliminados,
            cambios=cambios,
            sin_cambios=sin_cambios,
            estadisticas=estadisticas,
            alertas=[AlertaDTO.desde_entidad(a) for a in alertas],
            generado_en=generado_en,
        )
