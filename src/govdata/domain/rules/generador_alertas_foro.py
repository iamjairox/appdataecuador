"""Regla de dominio: generador de Alertas del Foro -- Submodulo 8.7.

Genera alerta cuando: Cambio de estado, Cambio de provincia, Cambio de
registro, Cambio de cualquier dato del Foro -- los 4 disparadores
pedidos, mas la simetria nuevo/eliminado (Submodulo 8.6, "nunca eliminar
informacion previa" -- una matricula que aparece o desaparece merece
alerta, no solo un cambio de dato)."""

from __future__ import annotations

from datetime import datetime

from govdata.application.dto.diferencia_registro_foro_dto import DiferenciaRegistroForoDTO
from govdata.domain.entities.alerta_foro import AlertaForo
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_foro import TipoAlertaForo
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo

_PRIORIDAD_POR_TIPO: dict[TipoAlertaForo, NivelCriticidad] = {
    TipoAlertaForo.REGISTRO_NUEVO: NivelCriticidad.MEDIO,
    TipoAlertaForo.REGISTRO_ELIMINADO: NivelCriticidad.ALTO,
    TipoAlertaForo.CAMBIO_ESTADO: NivelCriticidad.ALTO,
    TipoAlertaForo.CAMBIO_PROVINCIA: NivelCriticidad.MEDIO,
    TipoAlertaForo.CAMBIO_REGISTRO: NivelCriticidad.MEDIO,
    TipoAlertaForo.CAMBIO_DATO: NivelCriticidad.BAJO,
}
_TIPO_ALERTA_POR_TIPO_CAMBIO: dict[TipoCambioForo, TipoAlertaForo] = {
    TipoCambioForo.CAMBIO_ESTADO: TipoAlertaForo.CAMBIO_ESTADO,
    TipoCambioForo.CAMBIO_PROVINCIA: TipoAlertaForo.CAMBIO_PROVINCIA,
    TipoCambioForo.CAMBIO_REGISTRO: TipoAlertaForo.CAMBIO_REGISTRO,
    TipoCambioForo.CAMBIO_DATO: TipoAlertaForo.CAMBIO_DATO,
}


def _alerta(
    tipo: TipoAlertaForo, descripcion: str, persona_master_id: int, detectado_en: datetime,
    registro_foro_id: int | None,
) -> AlertaForo:
    return AlertaForo(
        persona_master_id=persona_master_id, tipo=tipo, prioridad=_PRIORIDAD_POR_TIPO[tipo],
        descripcion=descripcion, detectado_en=detectado_en, registro_foro_id=registro_foro_id,
    )


def generar_alertas_por_diferencia(
    diferencia: DiferenciaRegistroForoDTO, persona_master_id: int, detectado_en: datetime,
    registro_foro_id: int | None = None,
) -> list[AlertaForo]:
    if diferencia.tipo_cambio == TipoCambioForo.DATO_NUEVO and diferencia.datos_actuales is not None:
        return [
            _alerta(
                TipoAlertaForo.REGISTRO_NUEVO,
                f"Nuevo registro en el Foro de Abogados: {diferencia.datos_actuales.nombre_completo or diferencia.datos_actuales.registro}",
                persona_master_id, detectado_en, registro_foro_id,
            )
        ]

    if diferencia.tipo_cambio == TipoCambioForo.DATO_ELIMINADO and diferencia.datos_anteriores is not None:
        return [
            _alerta(
                TipoAlertaForo.REGISTRO_ELIMINADO,
                f"Registro eliminado del Foro de Abogados: {diferencia.datos_anteriores.nombre_completo or diferencia.datos_anteriores.registro}",
                persona_master_id, detectado_en, registro_foro_id,
            )
        ]

    tipo_alerta = _TIPO_ALERTA_POR_TIPO_CAMBIO.get(diferencia.tipo_cambio)
    if tipo_alerta is None:
        return []

    campos = ", ".join(f"{c.campo}: '{c.valor_anterior}' -> '{c.valor_nuevo}'" for c in diferencia.campos_modificados)
    return [_alerta(tipo_alerta, f"Cambio detectado en el Foro de Abogados ({campos})", persona_master_id, detectado_en, registro_foro_id)]
