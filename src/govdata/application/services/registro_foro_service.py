"""Servicio: RegistroForoService -- Submodulos 8.6 (Historial) y 8.14
(Versionado).

Unico lugar que abre/cierra `RegistroForoVersion` y mantiene
`RegistroForo` (el puntero vigente) sincronizado -- mismo principio que
`TituloAcademicoService` (Modulo 7): "nunca sobrescribir" -- la version
vigente anterior se cierra, se inserta una nueva, y se dedica un
`HistorialForo` a la diferencia concreta detectada."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime

from govdata.application.dto.diferencia_registro_foro_dto import DiferenciaRegistroForoDTO
from govdata.application.ports.historial_foro_repository_port import HistorialForoRepositoryPort
from govdata.application.ports.registro_foro_repository_port import RegistroForoRepositoryPort
from govdata.application.ports.registro_foro_version_repository_port import (
    RegistroForoVersionRepositoryPort,
)
from govdata.config.logging_config import get_logger
from govdata.domain.entities.historial_foro import HistorialForo
from govdata.domain.entities.registro_foro import RegistroForo
from govdata.domain.entities.registro_foro_version import RegistroForoVersion
from govdata.domain.rules.normalizador_foro import interpretar_estado_foro
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo

logger = get_logger(__name__)


def _descripcion(diferencia: DiferenciaRegistroForoDTO) -> str:
    if diferencia.tipo_cambio == TipoCambioForo.DATO_NUEVO and diferencia.datos_actuales:
        return f"Registro nuevo en el Foro: {diferencia.datos_actuales.nombre_completo or diferencia.datos_actuales.registro}"
    if diferencia.tipo_cambio == TipoCambioForo.DATO_ELIMINADO and diferencia.datos_anteriores:
        return f"Registro eliminado del Foro: {diferencia.datos_anteriores.nombre_completo or diferencia.datos_anteriores.registro}"
    campos = ", ".join(c.campo for c in diferencia.campos_modificados)
    return f"Cambio en: {campos}" if campos else diferencia.tipo_cambio.value


class RegistroForoService:
    def __init__(
        self,
        registro_repository: RegistroForoRepositoryPort,
        version_repository: RegistroForoVersionRepositoryPort,
        historial_repository: HistorialForoRepositoryPort,
    ) -> None:
        self._registro_repository = registro_repository
        self._version_repository = version_repository
        self._historial_repository = historial_repository

    def aplicar_diferencia(
        self,
        diferencia: DiferenciaRegistroForoDTO,
        persona_master_id: int,
        consulta_foro_id: int,
        fecha: date,
        consultado_en: datetime,
    ) -> RegistroForo | None:
        """Traduce UNA diferencia ya clasificada en una transicion de
        version + puntero vigente + entrada de historial. SIN_CAMBIOS no
        toca nada (nunca se reescribe una version sin motivo real)."""
        if diferencia.tipo_cambio == TipoCambioForo.SIN_CAMBIOS:
            return None

        if diferencia.tipo_cambio == TipoCambioForo.DATO_ELIMINADO:
            return self._aplicar_eliminado(diferencia, persona_master_id, consulta_foro_id, fecha, consultado_en)

        return self._aplicar_nuevo_o_cambio(diferencia, persona_master_id, consulta_foro_id, fecha, consultado_en)

    def _aplicar_eliminado(
        self, diferencia: DiferenciaRegistroForoDTO, persona_master_id: int, consulta_foro_id: int, fecha: date,
        consultado_en: datetime,
    ) -> RegistroForo | None:
        registro_vigente = self._registro_repository.buscar_vigente_por_clave(persona_master_id, diferencia.clave_registro)
        version_vigente = self._version_repository.buscar_vigente(persona_master_id, diferencia.clave_registro)

        if registro_vigente is not None:
            registro_vigente.cerrar()
            self._registro_repository.guardar(registro_vigente)
        if version_vigente is not None:
            version_vigente.cerrar(fecha)
            self._version_repository.guardar(version_vigente)

        self._registrar_historial(
            diferencia, persona_master_id, consulta_foro_id, consultado_en,
            registro_foro_id=registro_vigente.id if registro_vigente else None,
        )
        return registro_vigente

    def _aplicar_nuevo_o_cambio(
        self, diferencia: DiferenciaRegistroForoDTO, persona_master_id: int, consulta_foro_id: int, fecha: date,
        consultado_en: datetime,
    ) -> RegistroForo | None:
        datos = diferencia.datos_actuales
        if datos is None:
            return None

        cambio_de_clave = diferencia.clave_registro_anterior is not None
        clave_busqueda = diferencia.clave_registro_anterior or diferencia.clave_registro
        registro_existente = self._registro_repository.buscar_vigente_por_clave(persona_master_id, clave_busqueda)
        version_existente = self._version_repository.buscar_vigente(persona_master_id, clave_busqueda)

        siguiente_numero = 1
        if version_existente is not None:
            version_existente.cerrar(fecha)
            self._version_repository.guardar(version_existente)
            siguiente_numero = version_existente.numero_version + 1

        estado = interpretar_estado_foro(datos.estado)
        nueva_version = RegistroForoVersion(
            persona_master_id=persona_master_id, clave_registro=diferencia.clave_registro,
            numero_version=siguiente_numero, fecha_inicio=fecha, consulta_foro_id=consulta_foro_id,
            nombre_completo=datos.nombre_completo, registro=datos.registro, provincia=datos.provincia,
            estado=estado, cedula=datos.cedula,
        )
        self._version_repository.guardar(nueva_version)

        if registro_existente is not None and cambio_de_clave:
            # La CLAVE de identidad del registro cambio (tipicamente broto
            # un numero de registro) -- la fila vieja se cierra, nunca se
            # reutiliza bajo una clave distinta a la que fue creada.
            registro_existente.cerrar()
            self._registro_repository.guardar(registro_existente)
            registro_existente = None

        if registro_existente is not None:
            registro_existente.nombre_completo = datos.nombre_completo
            registro_existente.registro = datos.registro
            registro_existente.provincia = datos.provincia
            registro_existente.estado = estado
            registro_existente.cedula = datos.cedula
            registro_existente.correo_personal = datos.correo
            registro_existente.celular_personal = datos.celular
            registro_existente.numero_version = siguiente_numero
            registro_existente.evidencia = str(consulta_foro_id)
            registro_existente.fecha_consulta = consultado_en
            registro_actualizado = self._registro_repository.guardar(registro_existente)
        else:
            registro_actualizado = self._registro_repository.guardar(
                RegistroForo(
                    persona_master_id=persona_master_id, clave_registro=diferencia.clave_registro,
                    nombre_completo=datos.nombre_completo, registro=datos.registro, provincia=datos.provincia,
                    estado=estado, cedula=datos.cedula, correo_personal=datos.correo,
                    celular_personal=datos.celular, numero_version=siguiente_numero,
                    evidencia=str(consulta_foro_id), fecha_consulta=consultado_en,
                )
            )

        self._registrar_historial(
            diferencia, persona_master_id, consulta_foro_id, consultado_en, registro_foro_id=registro_actualizado.id
        )
        logger.info(
            "registro_foro_version_abierta", persona_master_id=persona_master_id, clave_registro=diferencia.clave_registro,
            numero_version=siguiente_numero, tipo_cambio=diferencia.tipo_cambio.value,
        )
        return registro_actualizado

    def _registrar_historial(
        self, diferencia: DiferenciaRegistroForoDTO, persona_master_id: int, consulta_foro_id: int,
        detectado_en: datetime, registro_foro_id: int | None,
    ) -> None:
        registro = HistorialForo(
            persona_master_id=persona_master_id, clave_registro=diferencia.clave_registro,
            tipo_cambio=diferencia.tipo_cambio, detectado_en=detectado_en, consulta_foro_id=consulta_foro_id,
            registro_foro_id=registro_foro_id,
            campos_modificados=[asdict(c) for c in diferencia.campos_modificados],
            descripcion=_descripcion(diferencia),
        )
        self._historial_repository.guardar_lote([registro])
