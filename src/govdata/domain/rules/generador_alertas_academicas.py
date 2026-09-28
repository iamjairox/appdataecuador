"""Regla de dominio: generador de Alertas Academicas -- Submodulo 7.8.

Genera alerta cuando: Nuevo titulo, Titulo eliminado, Registro
suspendido, Registro anulado, Cambio de nivel, Cambio de institucion,
Cambio de estado -- exactamente los 7 disparadores pedidos. Un
`CAMBIO_MULTIPLE` (Submodulo 7.7) puede generar VARIAS alertas a la vez
(una por cada campo relevante que cambio), nunca se pierde ninguna.
"""

from __future__ import annotations

from datetime import datetime

from govdata.application.dto.diferencia_titulo_dto import DiferenciaTituloDTO
from govdata.domain.entities.alerta_academica import AlertaAcademica
from govdata.domain.rules.normalizacion import normalizar_texto
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_academica import TipoAlertaAcademica
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico

_PRIORIDAD_POR_TIPO: dict[TipoAlertaAcademica, NivelCriticidad] = {
    TipoAlertaAcademica.NUEVO_TITULO: NivelCriticidad.MEDIO,
    TipoAlertaAcademica.TITULO_ELIMINADO: NivelCriticidad.ALTO,
    TipoAlertaAcademica.CAMBIO_NIVEL: NivelCriticidad.MEDIO,
    TipoAlertaAcademica.CAMBIO_INSTITUCION: NivelCriticidad.MEDIO,
    TipoAlertaAcademica.CAMBIO_ESTADO: NivelCriticidad.ALTO,
    TipoAlertaAcademica.REGISTRO_SUSPENDIDO: NivelCriticidad.CRITICO,
    TipoAlertaAcademica.REGISTRO_ANULADO: NivelCriticidad.CRITICO,
}


def _alerta(
    tipo: TipoAlertaAcademica, descripcion: str, persona_master_id: int, detectado_en: datetime,
    titulo_academico_id: int | None,
) -> AlertaAcademica:
    return AlertaAcademica(
        persona_master_id=persona_master_id, tipo=tipo, prioridad=_PRIORIDAD_POR_TIPO[tipo],
        descripcion=descripcion, detectado_en=detectado_en, titulo_academico_id=titulo_academico_id,
    )


def generar_alertas_por_diferencia(
    diferencia: DiferenciaTituloDTO, persona_master_id: int, detectado_en: datetime,
    titulo_academico_id: int | None = None,
) -> list[AlertaAcademica]:
    alertas: list[AlertaAcademica] = []

    if diferencia.tipo_cambio == TipoCambioAcademico.TITULO_NUEVO and diferencia.datos_actuales is not None:
        alertas.append(
            _alerta(
                TipoAlertaAcademica.NUEVO_TITULO, f"Nuevo titulo detectado: {diferencia.datos_actuales.titulo}",
                persona_master_id, detectado_en, titulo_academico_id,
            )
        )
        return alertas

    if diferencia.tipo_cambio == TipoCambioAcademico.TITULO_ELIMINADO and diferencia.datos_anteriores is not None:
        alertas.append(
            _alerta(
                TipoAlertaAcademica.TITULO_ELIMINADO, f"Titulo eliminado: {diferencia.datos_anteriores.titulo}",
                persona_master_id, detectado_en, titulo_academico_id,
            )
        )
        return alertas

    campos = {c.campo: c for c in diferencia.campos_modificados}

    if "nivel" in campos:
        c = campos["nivel"]
        alertas.append(
            _alerta(
                TipoAlertaAcademica.CAMBIO_NIVEL, f"Cambio de nivel: '{c.valor_anterior}' -> '{c.valor_nuevo}'",
                persona_master_id, detectado_en, titulo_academico_id,
            )
        )

    if "institucion" in campos:
        c = campos["institucion"]
        alertas.append(
            _alerta(
                TipoAlertaAcademica.CAMBIO_INSTITUCION,
                f"Cambio de institucion: '{c.valor_anterior}' -> '{c.valor_nuevo}'",
                persona_master_id, detectado_en, titulo_academico_id,
            )
        )

    if "estado" in campos:
        c = campos["estado"]
        alertas.append(
            _alerta(
                TipoAlertaAcademica.CAMBIO_ESTADO, f"Cambio de estado: '{c.valor_anterior}' -> '{c.valor_nuevo}'",
                persona_master_id, detectado_en, titulo_academico_id,
            )
        )
        estado_normalizado = normalizar_texto(c.valor_nuevo) if c.valor_nuevo else ""
        if estado_normalizado == "SUSPENDIDO":
            alertas.append(
                _alerta(
                    TipoAlertaAcademica.REGISTRO_SUSPENDIDO, "Registro academico suspendido",
                    persona_master_id, detectado_en, titulo_academico_id,
                )
            )
        elif estado_normalizado == "ANULADO":
            alertas.append(
                _alerta(
                    TipoAlertaAcademica.REGISTRO_ANULADO, "Registro academico anulado",
                    persona_master_id, detectado_en, titulo_academico_id,
                )
            )

    return alertas
