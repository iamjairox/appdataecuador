"""Regla de dominio: generador de Eventos Academicos -- Submodulo 7.9.

`TITULO_NUEVO`/`TITULO_ELIMINADO`/`CAMBIO_NIVEL`/`CAMBIO_UNIVERSIDAD`/
`CAMBIO_ESTADO` se derivan de una `DiferenciaTituloDTO` (igual que las
alertas, un `CAMBIO_MULTIPLE` puede producir varios eventos a la vez).
`CONSULTA_EXITOSA`/`CONSULTA_FALLIDA` son eventos sobre la consulta en si
(Submodulo 7.15), no sobre un titulo -- se generan aparte.
"""

from __future__ import annotations

from datetime import datetime

from govdata.application.dto.diferencia_titulo_dto import DiferenciaTituloDTO
from govdata.domain.entities.evento_academico import EventoAcademico
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico
from govdata.domain.value_objects.tipo_evento_academico import TipoEventoAcademico


def generar_eventos_por_diferencia(
    diferencia: DiferenciaTituloDTO, persona_master_id: int, detectado_en: datetime
) -> list[EventoAcademico]:
    eventos: list[EventoAcademico] = []

    if diferencia.tipo_cambio == TipoCambioAcademico.TITULO_NUEVO:
        eventos.append(
            EventoAcademico(
                tipo=TipoEventoAcademico.TITULO_NUEVO, persona_master_id=persona_master_id,
                payload={"clave_titulo": diferencia.clave_titulo}, creado_en=detectado_en,
            )
        )
        return eventos

    if diferencia.tipo_cambio == TipoCambioAcademico.TITULO_ELIMINADO:
        eventos.append(
            EventoAcademico(
                tipo=TipoEventoAcademico.TITULO_ELIMINADO, persona_master_id=persona_master_id,
                payload={"clave_titulo": diferencia.clave_titulo}, creado_en=detectado_en,
            )
        )
        return eventos

    campos = {c.campo for c in diferencia.campos_modificados}
    if "nivel" in campos:
        eventos.append(
            EventoAcademico(
                tipo=TipoEventoAcademico.CAMBIO_NIVEL, persona_master_id=persona_master_id,
                payload={"clave_titulo": diferencia.clave_titulo}, creado_en=detectado_en,
            )
        )
    if "institucion" in campos:
        eventos.append(
            EventoAcademico(
                tipo=TipoEventoAcademico.CAMBIO_UNIVERSIDAD, persona_master_id=persona_master_id,
                payload={"clave_titulo": diferencia.clave_titulo}, creado_en=detectado_en,
            )
        )
    if "estado" in campos:
        eventos.append(
            EventoAcademico(
                tipo=TipoEventoAcademico.CAMBIO_ESTADO, persona_master_id=persona_master_id,
                payload={"clave_titulo": diferencia.clave_titulo}, creado_en=detectado_en,
            )
        )
    return eventos


def generar_evento_consulta_exitosa(persona_master_id: int, cuando: datetime, titulos_encontrados: int) -> EventoAcademico:
    return EventoAcademico(
        tipo=TipoEventoAcademico.CONSULTA_EXITOSA, persona_master_id=persona_master_id,
        payload={"titulos_encontrados": titulos_encontrados}, creado_en=cuando,
    )


def generar_evento_consulta_fallida(persona_master_id: int, cuando: datetime, error: str) -> EventoAcademico:
    return EventoAcademico(
        tipo=TipoEventoAcademico.CONSULTA_FALLIDA, persona_master_id=persona_master_id,
        payload={"error": error}, creado_en=cuando,
    )
