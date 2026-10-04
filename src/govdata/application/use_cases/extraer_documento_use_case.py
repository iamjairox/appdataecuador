"""Caso de uso: ExtraerDocumentoUseCase.

Orquesta el Motor de Extraccion completo para UN documento ya descargado
(Modulo 3): Parser (4.1) -> Normalizador (4.2) -> Clasificador (4.3) ->
Fingerprint (4.4) -> Persistencia (Persona/Funcionario). Termina
produciendo exactamente el contrato oficial `ResultadoUnificadoDTO`
(Submodulo 4.10).

Nunca detiene el pipeline por una fila individual: documento corrupto,
PDF vacio, columnas inexistentes, correo/telefono invalidos, cargo o
dependencia desconocidos -- todos se degradan a "esta fila se descarta"
o "este campo queda vacio", nunca a una excepcion que tumbe el documento
completo. Solo un documento genuinamente ilegible (`EstadoParseo.ERROR`)
o que requiera OCR interrumpe ESTE documento (nunca otros).
"""

from __future__ import annotations

import time
from datetime import UTC, date, datetime

from govdata.application.dto.fila_extraida_dto import FilaExtraidaDTO
from govdata.application.dto.resultado_parseo_dto import EstadoParseo
from govdata.application.dto.resultado_unificado_dto import (
    DocumentoResumenDTO,
    EntidadResumenDTO,
    FuncionarioUnificadoDTO,
    ResultadoUnificadoDTO,
)
from govdata.application.ports.funcionario_repository_port import FuncionarioRepositoryPort
from govdata.application.ports.persona_repository_port import PersonaRepositoryPort
from govdata.application.services.parser_factory import ParserFactory
from govdata.application.services.progreso_listado_service import progreso_listados
from govdata.config.logging_config import get_logger
from govdata.domain.entities.documento import DocumentoTransparencia
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import (
    ExtraccionFallidaError,
    FuncionarioInvalidoError,
    GovDataError,
)
from govdata.domain.rules.clasificador_funcionarios import clasificar_funcionario
from govdata.domain.rules.generador_fingerprint import generar_fingerprint
from govdata.domain.rules.normalizador_universal import normalizar_tabla
from govdata.domain.rules.reglas_configurables import RuleEngine
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.cargo import Cargo
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.telefono import Telefono

logger = get_logger(__name__)

_DEPENDENCIA_DESCONOCIDA = "(dependencia no especificada)"


class DocumentoRequiereOcrError(GovDataError):
    """El documento es un PDF escaneado -- pendiente para el futuro Modulo OCR."""


class ExtraerDocumentoUseCase:
    def __init__(
        self,
        parser_factory: ParserFactory,
        rule_engine: RuleEngine,
        persona_repository: PersonaRepositoryPort,
        funcionario_repository: FuncionarioRepositoryPort,
    ) -> None:
        self._parser_factory = parser_factory
        self._rule_engine = rule_engine
        self._persona_repository = persona_repository
        self._funcionario_repository = funcionario_repository

    def ejecutar(
        self,
        entidad: Entidad,
        documento: DocumentoTransparencia,
        ruta_archivo_local: str,
        mes_publicado: date,
    ) -> ResultadoUnificadoDTO:
        if documento.id is None or entidad.id is None:
            raise ExtraccionFallidaError("Entidad y Documento requieren id para extraer (persistalos primero)")

        inicio_parser = time.perf_counter()
        parser = self._parser_factory.obtener_parser(documento.tipo_archivo)
        resultado_parseo = parser.extraer(ruta_archivo_local)
        duracion_parser = time.perf_counter() - inicio_parser

        if resultado_parseo.estado == EstadoParseo.REQUIERE_OCR:
            logger.warning("documento_requiere_ocr", documento_id=documento.id, duracion_segundos=round(duracion_parser, 3))
            raise DocumentoRequiereOcrError(
                f"Documento {documento.id} requiere OCR: {resultado_parseo.mensaje}"
            )
        if resultado_parseo.estado == EstadoParseo.ERROR or resultado_parseo.tabla is None:
            raise ExtraccionFallidaError(
                f"No se pudo extraer el documento {documento.id}: {resultado_parseo.mensaje}"
            )

        logger.info(
            "parser_completado",
            documento_id=documento.id,
            duracion_segundos=round(duracion_parser, 3),
            filas_crudas=resultado_parseo.tabla.cantidad_filas,
        )

        inicio_pipeline = time.perf_counter()
        filas_normalizadas = normalizar_tabla(resultado_parseo.tabla, self._rule_engine.normalizacion)
        progreso_listados.establecer_total(entidad.id, len(filas_normalizadas))

        funcionarios_dto: list[FuncionarioUnificadoDTO] = []
        cantidad_descartados = 0
        cantidad_errores = 0

        for indice, fila in enumerate(filas_normalizadas, start=1):
            try:
                resultado_fila = self._procesar_fila(fila, entidad.id, documento.id)
            except GovDataError as exc:
                cantidad_errores += 1
                logger.warning("fila_descartada_por_error", documento_id=documento.id, error=str(exc))
            else:
                if resultado_fila is None:
                    cantidad_descartados += 1
                else:
                    funcionarios_dto.append(resultado_fila)

            # Publica avance real cada 50 filas para no convertir el
            # seguimiento en otra carga relevante sobre la aplicación.
            if indice % 50 == 0 or indice == len(filas_normalizadas):
                progreso_listados.actualizar(entidad.id, indice, len(funcionarios_dto))

        duracion_pipeline = time.perf_counter() - inicio_pipeline
        logger.info(
            "documento_extraido",
            documento_id=documento.id,
            filas_crudas=resultado_parseo.tabla.cantidad_filas,
            filas_normalizadas=len(filas_normalizadas),
            clasificados=len(funcionarios_dto),
            descartados=cantidad_descartados,
            errores=cantidad_errores,
            duracion_segundos=round(duracion_pipeline, 3),
            duracion_por_funcionario_segundos=(
                round(duracion_pipeline / len(filas_normalizadas), 5) if filas_normalizadas else 0.0
            ),
        )

        return ResultadoUnificadoDTO(
            entidad=EntidadResumenDTO(
                id=entidad.id,
                nombre=entidad.nombre,
                portal_origen=entidad.portal_origen,
                identificador_portal=entidad.metadata_extra.get("identificador_portal"),
            ),
            documento=DocumentoResumenDTO(
                id=documento.id,
                tipo_archivo=documento.tipo_archivo.value,
                mes_publicado=mes_publicado,
                hash_sha256=documento.hash_sha256 or "",
                version=documento.version,
                url=documento.url_documento,
            ),
            funcionarios=funcionarios_dto,
            generado_en=datetime.now(UTC),
        )

    def _procesar_fila(
        self, fila: FilaExtraidaDTO, entidad_id: int, documento_id: int
    ) -> FuncionarioUnificadoDTO | None:
        clasificado = clasificar_funcionario(fila, self._rule_engine.clasificacion)
        if clasificado is None:
            return None

        fingerprint, fingerprint_hash = generar_fingerprint(fila.nombres, fila.apellidos)
        clasificado = clasificado.con_fingerprint(fingerprint, fingerprint_hash)

        persona = self._buscar_o_crear_persona(fila, fingerprint, fingerprint_hash)

        # Una reextraccion del mismo documento actualiza la ficha vigente en
        # vez de crear una segunda fila para la misma persona y entidad.
        existente = self._funcionario_repository.buscar_vigente(persona.id, entidad_id)  # type: ignore[arg-type]
        funcionario = Funcionario(
            persona_id=persona.id,  # type: ignore[arg-type]
            entidad_id=entidad_id,
            cargo=Cargo(fila.cargo or clasificado.cargo_normalizado),
            dependencia=fila.dependencia or _DEPENDENCIA_DESCONOCIDA,
            area_clasificada=AreaRelevante(clasificado.area),
            id=existente.id if existente else None,
            score_clasificacion=clasificado.score,
            documento_id=documento_id,
        )
        try:
            self._funcionario_repository.guardar(funcionario)
        except FuncionarioInvalidoError as exc:
            raise ExtraccionFallidaError(f"Funcionario invalido para '{fila.nombres} {fila.apellidos}': {exc}") from exc

        return FuncionarioUnificadoDTO(
            nombre=fila.nombres,
            apellido=fila.apellidos,
            cargo=str(funcionario.cargo),
            dependencia=funcionario.dependencia,
            # Correo/telefono VALIDADOS (Value Objects), no los crudos de
            # `fila` -- deben coincidir con lo que realmente quedo
            # persistido en `Persona` (ver `_buscar_o_crear_persona`).
            correo=str(persona.correo) if persona.correo else None,
            telefono=str(persona.telefono) if persona.telefono else None,
            area=clasificado.area,
            score=round(clasificado.score, 2),
            fingerprint=fingerprint,
        )

    def _buscar_o_crear_persona(self, fila: FilaExtraidaDTO, fingerprint: str, fingerprint_hash: str) -> Persona:
        correo = Correo.crear_opcional(fila.correo)
        telefono = Telefono.crear_opcional(fila.telefono)

        persona = self._persona_repository.buscar_por_fingerprint_hash(fingerprint_hash)
        if persona is None:
            persona = Persona(
                nombre_completo=NombreCompleto(nombres=fila.nombres, apellidos=fila.apellidos),
                correo=correo,
                telefono=telefono,
                extension_telefonica=fila.extension_telefonica,
                fingerprint=fingerprint,
                fingerprint_hash=fingerprint_hash,
            )
        else:
            persona.actualizar_datos_contacto(correo, telefono, fila.extension_telefonica)
        return self._persona_repository.guardar(persona)
