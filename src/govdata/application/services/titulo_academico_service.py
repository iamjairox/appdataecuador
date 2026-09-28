"""Servicio: TituloAcademicoService -- Submodulos 7.6 (Historial
Academico) y 7.14 (Versionado).

Unico lugar que abre/cierra `TituloVersionAcademica` y mantiene
`TituloAcademico` (el puntero vigente) sincronizado -- mismo principio
que `HistorialService` (Modulo 5) y `RegistroFuenteService` (Modulo 6):
"nunca sobrescribir" -- la version vigente anterior se cierra, se
inserta una nueva, y se dedica un `HistorialAcademico` a la diferencia
concreta detectada.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime

from govdata.application.dto.diferencia_titulo_dto import DiferenciaTituloDTO
from govdata.application.ports.historial_academico_repository_port import (
    HistorialAcademicoRepositoryPort,
)
from govdata.application.ports.titulo_academico_repository_port import (
    TituloAcademicoRepositoryPort,
)
from govdata.application.ports.titulo_version_repository_port import TituloVersionRepositoryPort
from govdata.config.logging_config import get_logger
from govdata.domain.entities.historial_academico import HistorialAcademico
from govdata.domain.entities.titulo_academico import TituloAcademico
from govdata.domain.entities.titulo_version_academica import TituloVersionAcademica
from govdata.domain.rules.normalizador_academico import interpretar_estado_registro
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico

logger = get_logger(__name__)


def _descripcion(diferencia: DiferenciaTituloDTO) -> str:
    if diferencia.tipo_cambio == TipoCambioAcademico.TITULO_NUEVO and diferencia.datos_actuales:
        return f"Titulo nuevo: {diferencia.datos_actuales.titulo} ({diferencia.datos_actuales.institucion})"
    if diferencia.tipo_cambio == TipoCambioAcademico.TITULO_ELIMINADO and diferencia.datos_anteriores:
        return f"Titulo eliminado: {diferencia.datos_anteriores.titulo}"
    campos = ", ".join(c.campo for c in diferencia.campos_modificados)
    return f"Cambio en: {campos}" if campos else diferencia.tipo_cambio.value


class TituloAcademicoService:
    def __init__(
        self,
        titulo_repository: TituloAcademicoRepositoryPort,
        version_repository: TituloVersionRepositoryPort,
        historial_repository: HistorialAcademicoRepositoryPort,
    ) -> None:
        self._titulo_repository = titulo_repository
        self._version_repository = version_repository
        self._historial_repository = historial_repository

    def aplicar_diferencia(
        self,
        diferencia: DiferenciaTituloDTO,
        persona_master_id: int,
        consulta_senescyt_id: int,
        fecha: date,
        consultado_en: datetime,
    ) -> TituloAcademico | None:
        """Traduce UNA diferencia ya clasificada en una transicion de
        version + puntero vigente + entrada de historial. SIN_CAMBIOS no
        toca nada (nunca se reescribe una version sin motivo real)."""
        if diferencia.tipo_cambio == TipoCambioAcademico.SIN_CAMBIOS:
            return None

        if diferencia.tipo_cambio == TipoCambioAcademico.TITULO_ELIMINADO:
            return self._aplicar_eliminado(diferencia, persona_master_id, consulta_senescyt_id, fecha, consultado_en)

        return self._aplicar_nuevo_o_cambio(diferencia, persona_master_id, consulta_senescyt_id, fecha, consultado_en)

    def _aplicar_eliminado(
        self, diferencia: DiferenciaTituloDTO, persona_master_id: int, consulta_senescyt_id: int, fecha: date,
        consultado_en: datetime,
    ) -> TituloAcademico | None:
        titulo_vigente = self._titulo_repository.buscar_vigente_por_clave(persona_master_id, diferencia.clave_titulo)
        version_vigente = self._version_repository.buscar_vigente(persona_master_id, diferencia.clave_titulo)

        if titulo_vigente is not None:
            titulo_vigente.cerrar()
            self._titulo_repository.guardar(titulo_vigente)
        if version_vigente is not None:
            version_vigente.cerrar(fecha)
            self._version_repository.guardar(version_vigente)

        self._registrar_historial(
            diferencia, persona_master_id, consulta_senescyt_id, consultado_en,
            titulo_academico_id=titulo_vigente.id if titulo_vigente else None,
        )
        return titulo_vigente

    def _aplicar_nuevo_o_cambio(
        self, diferencia: DiferenciaTituloDTO, persona_master_id: int, consulta_senescyt_id: int, fecha: date,
        consultado_en: datetime,
    ) -> TituloAcademico | None:
        datos = diferencia.datos_actuales
        if datos is None:
            return None

        cambio_de_clave = diferencia.clave_titulo_anterior is not None
        clave_busqueda = diferencia.clave_titulo_anterior or diferencia.clave_titulo
        titulo_existente = self._titulo_repository.buscar_vigente_por_clave(persona_master_id, clave_busqueda)
        version_existente = self._version_repository.buscar_vigente(persona_master_id, clave_busqueda)

        siguiente_numero = 1
        if version_existente is not None:
            version_existente.cerrar(fecha)
            self._version_repository.guardar(version_existente)
            siguiente_numero = version_existente.numero_version + 1

        estado = interpretar_estado_registro(datos.estado)
        nueva_version = TituloVersionAcademica(
            persona_master_id=persona_master_id, clave_titulo=diferencia.clave_titulo,
            numero_version=siguiente_numero, titulo=datos.titulo, nivel=datos.nivel, institucion=datos.institucion,
            fecha_inicio=fecha, consulta_senescyt_id=consulta_senescyt_id, fecha_registro=datos.fecha_registro,
            pais=datos.pais, estado=estado, modalidad=datos.modalidad, numero_registro=datos.numero_registro,
            area_conocimiento=datos.area_conocimiento, tipo_titulo=datos.tipo_titulo,
            fecha_graduacion=datos.fecha_graduacion, observaciones=datos.observaciones,
        )
        self._version_repository.guardar(nueva_version)

        if titulo_existente is not None and cambio_de_clave:
            # La CLAVE de identidad del titulo cambio (tipicamente broto
            # un numero_registro) -- la fila vieja se cierra, nunca se
            # reutiliza bajo una clave distinta a la que fue creada.
            titulo_existente.cerrar()
            self._titulo_repository.guardar(titulo_existente)
            titulo_existente = None

        if titulo_existente is not None:
            titulo_existente.titulo = datos.titulo
            titulo_existente.nivel = datos.nivel
            titulo_existente.institucion = datos.institucion
            titulo_existente.fecha_registro = datos.fecha_registro
            titulo_existente.pais = datos.pais
            titulo_existente.estado = estado
            titulo_existente.modalidad = datos.modalidad
            titulo_existente.numero_registro = datos.numero_registro
            titulo_existente.area_conocimiento = datos.area_conocimiento
            titulo_existente.tipo_titulo = datos.tipo_titulo
            titulo_existente.fecha_graduacion = datos.fecha_graduacion
            titulo_existente.observaciones = datos.observaciones
            titulo_existente.numero_version = siguiente_numero
            titulo_existente.evidencia = str(consulta_senescyt_id)
            titulo_existente.fecha_consulta = consultado_en
            titulo_actualizado = self._titulo_repository.guardar(titulo_existente)
        else:
            titulo_actualizado = self._titulo_repository.guardar(
                TituloAcademico(
                    persona_master_id=persona_master_id, clave_titulo=diferencia.clave_titulo, titulo=datos.titulo,
                    nivel=datos.nivel, institucion=datos.institucion, fecha_registro=datos.fecha_registro,
                    pais=datos.pais, estado=estado, modalidad=datos.modalidad, numero_registro=datos.numero_registro,
                    area_conocimiento=datos.area_conocimiento, tipo_titulo=datos.tipo_titulo,
                    fecha_graduacion=datos.fecha_graduacion, observaciones=datos.observaciones,
                    numero_version=siguiente_numero, evidencia=str(consulta_senescyt_id), fecha_consulta=consultado_en,
                )
            )

        self._registrar_historial(
            diferencia, persona_master_id, consulta_senescyt_id, consultado_en, titulo_academico_id=titulo_actualizado.id
        )
        logger.info(
            "titulo_version_abierta", persona_master_id=persona_master_id, clave_titulo=diferencia.clave_titulo,
            numero_version=siguiente_numero, tipo_cambio=diferencia.tipo_cambio.value,
        )
        return titulo_actualizado

    def _registrar_historial(
        self, diferencia: DiferenciaTituloDTO, persona_master_id: int, consulta_senescyt_id: int,
        detectado_en: datetime, titulo_academico_id: int | None,
    ) -> None:
        registro = HistorialAcademico(
            persona_master_id=persona_master_id, clave_titulo=diferencia.clave_titulo,
            tipo_cambio=diferencia.tipo_cambio, detectado_en=detectado_en, consulta_senescyt_id=consulta_senescyt_id,
            titulo_academico_id=titulo_academico_id,
            campos_modificados=[asdict(c) for c in diferencia.campos_modificados],
            descripcion=_descripcion(diferencia),
        )
        self._historial_repository.guardar_lote([registro])
