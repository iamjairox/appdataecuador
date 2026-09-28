"""Regla de dominio: generador de Eventos del Foro -- Submodulo 8.7.

`REGISTRO_NUEVO`/`REGISTRO_ELIMINADO`/`CAMBIO_ESTADO`/`CAMBIO_PROVINCIA`/
`CAMBIO_REGISTRO`/`CAMBIO_DATO` se derivan de una
`DiferenciaRegistroForoDTO`. `CONSULTA_EXITOSA`/`CONSULTA_FALLIDA` son
eventos sobre la consulta en si (Submodulo 8.17), no sobre un registro --
se generan aparte, mismo patron que `generador_eventos_academicos.py`
(Modulo 7)."""

from __future__ import annotations

from datetime import datetime

from govdata.application.dto.diferencia_registro_foro_dto import DiferenciaRegistroForoDTO
from govdata.domain.entities.evento_foro import EventoForo
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo
from govdata.domain.value_objects.tipo_evento_foro import TipoEventoForo

_TIPO_EVENTO_POR_TIPO_CAMBIO: dict[TipoCambioForo, TipoEventoForo] = {
    TipoCambioForo.DATO_NUEVO: TipoEventoForo.REGISTRO_NUEVO,
    TipoCambioForo.DATO_ELIMINADO: TipoEventoForo.REGISTRO_ELIMINADO,
    TipoCambioForo.CAMBIO_ESTADO: TipoEventoForo.CAMBIO_ESTADO,
    TipoCambioForo.CAMBIO_PROVINCIA: TipoEventoForo.CAMBIO_PROVINCIA,
    TipoCambioForo.CAMBIO_REGISTRO: TipoEventoForo.CAMBIO_REGISTRO,
    TipoCambioForo.CAMBIO_DATO: TipoEventoForo.CAMBIO_DATO,
}


def generar_eventos_por_diferencia(
    diferencia: DiferenciaRegistroForoDTO, persona_master_id: int, detectado_en: datetime
) -> list[EventoForo]:
    tipo_evento = _TIPO_EVENTO_POR_TIPO_CAMBIO.get(diferencia.tipo_cambio)
    if tipo_evento is None:
        return []
    return [
        EventoForo(
            tipo=tipo_evento, persona_master_id=persona_master_id,
            payload={"clave_registro": diferencia.clave_registro}, creado_en=detectado_en,
        )
    ]


def generar_evento_consulta_exitosa(persona_master_id: int, cuando: datetime, registros_encontrados: int) -> EventoForo:
    return EventoForo(
        tipo=TipoEventoForo.CONSULTA_EXITOSA, persona_master_id=persona_master_id,
        payload={"registros_encontrados": registros_encontrados}, creado_en=cuando,
    )


def generar_evento_consulta_fallida(persona_master_id: int, cuando: datetime, error: str) -> EventoForo:
    return EventoForo(
        tipo=TipoEventoForo.CONSULTA_FALLIDA, persona_master_id=persona_master_id,
        payload={"error": error}, creado_en=cuando,
    )
