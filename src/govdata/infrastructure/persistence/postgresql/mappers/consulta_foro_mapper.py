"""Mapper: ConsultaForoModel <-> ConsultaForo (dominio)."""

from __future__ import annotations

from govdata.domain.entities.consulta_foro import ConsultaForo
from govdata.infrastructure.persistence.postgresql.models.consulta_foro_model import (
    ConsultaForoModel,
)


def a_dominio(modelo: ConsultaForoModel) -> ConsultaForo:
    return ConsultaForo(
        id=modelo.id, persona_master_id=modelo.persona_master_id, iniciado_en=modelo.iniciado_en,
        finalizado_en=modelo.finalizado_en, exito=modelo.exito, duracion_segundos=modelo.duracion_segundos,
        error=modelo.error, reintentos=modelo.reintentos, cache_utilizado=modelo.cache_utilizado,
        version_resultante=modelo.version_resultante, respuesta_cruda=modelo.respuesta_cruda,
        codigo_http=modelo.codigo_http, captcha_detectado=modelo.captcha_detectado,
        pagina_vacia=modelo.pagina_vacia, usuario=modelo.usuario, job_id=modelo.job_id,
    )


def a_modelo(consulta: ConsultaForo, modelo: ConsultaForoModel | None = None) -> ConsultaForoModel:
    modelo = modelo or ConsultaForoModel()
    if consulta.id is not None:
        modelo.id = consulta.id
    modelo.persona_master_id = consulta.persona_master_id
    modelo.iniciado_en = consulta.iniciado_en
    modelo.finalizado_en = consulta.finalizado_en
    modelo.exito = consulta.exito
    modelo.duracion_segundos = consulta.duracion_segundos
    modelo.error = consulta.error
    modelo.reintentos = consulta.reintentos
    modelo.cache_utilizado = consulta.cache_utilizado
    modelo.version_resultante = consulta.version_resultante
    modelo.respuesta_cruda = consulta.respuesta_cruda
    modelo.codigo_http = consulta.codigo_http
    modelo.captcha_detectado = consulta.captcha_detectado
    modelo.pagina_vacia = consulta.pagina_vacia
    modelo.usuario = consulta.usuario
    modelo.job_id = consulta.job_id
    return modelo
