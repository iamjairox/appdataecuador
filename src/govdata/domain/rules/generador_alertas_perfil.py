"""Regla de dominio: generador de Alertas de Perfil -- Submodulo 6.13.

Traduce un "campo cambio de X a Y" (detectado al registrar una nueva
version de `RegistroFuente`, Submodulo 6.9) a una `AlertaPerfil`
tipificada, con la prioridad configurada para ese tipo de cambio.
Campos no reconocidos, o sin cambio real, no generan alerta.
"""

from __future__ import annotations

from datetime import datetime

from govdata.domain.entities.alerta_perfil import AlertaPerfil
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_perfil import TipoAlertaPerfil

_MAPA_CAMPO_TIPO: dict[str, TipoAlertaPerfil] = {
    "titulo": TipoAlertaPerfil.TITULO_CAMBIADO,
    "maestria": TipoAlertaPerfil.NUEVA_MAESTRIA,
    "especializacion": TipoAlertaPerfil.NUEVA_ESPECIALIZACION,
    "correo": TipoAlertaPerfil.CAMBIO_CORREO_PERFIL,
    "institucion": TipoAlertaPerfil.NUEVA_INSTITUCION,
    "profesion": TipoAlertaPerfil.CAMBIO_PROFESION,
}

_PRIORIDAD_POR_TIPO: dict[TipoAlertaPerfil, NivelCriticidad] = {
    TipoAlertaPerfil.TITULO_CAMBIADO: NivelCriticidad.MEDIO,
    TipoAlertaPerfil.NUEVA_MAESTRIA: NivelCriticidad.ALTO,
    TipoAlertaPerfil.NUEVA_ESPECIALIZACION: NivelCriticidad.ALTO,
    TipoAlertaPerfil.CAMBIO_CORREO_PERFIL: NivelCriticidad.MEDIO,
    TipoAlertaPerfil.NUEVA_INSTITUCION: NivelCriticidad.MEDIO,
    TipoAlertaPerfil.CAMBIO_PROFESION: NivelCriticidad.ALTO,
}


def generar_alerta_por_cambio(
    campo: str,
    valor_anterior: str | None,
    valor_nuevo: str | None,
    persona_master_id: int,
    detectado_en: datetime,
    registro_fuente_id: int | None = None,
) -> AlertaPerfil | None:
    tipo = _MAPA_CAMPO_TIPO.get(campo)
    if tipo is None or not valor_nuevo or valor_anterior == valor_nuevo:
        return None
    descripcion = f"Campo '{campo}' cambio de '{valor_anterior or '(vacio)'}' a '{valor_nuevo}'"
    return AlertaPerfil(
        persona_master_id=persona_master_id,
        tipo=tipo,
        prioridad=_PRIORIDAD_POR_TIPO[tipo],
        descripcion=descripcion,
        detectado_en=detectado_en,
        registro_fuente_id=registro_fuente_id,
    )


def generar_alertas_por_cambios(
    cambios: dict[str, tuple[str | None, str | None]],
    persona_master_id: int,
    detectado_en: datetime,
    registro_fuente_id: int | None = None,
) -> list[AlertaPerfil]:
    """`cambios` es `{campo: (valor_anterior, valor_nuevo)}`, tipicamente
    el resultado de diferenciar dos `RegistroFuente.datos` consecutivos."""
    alertas = []
    for campo, (anterior, nuevo) in cambios.items():
        alerta = generar_alerta_por_cambio(campo, anterior, nuevo, persona_master_id, detectado_en, registro_fuente_id)
        if alerta is not None:
            alertas.append(alerta)
    return alertas
