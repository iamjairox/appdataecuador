"""Mapper: AuditoriaEtapaModel <-> AuditoriaEtapa (dominio)."""

from __future__ import annotations

import uuid

from govdata.domain.entities.auditoria_etapa import AuditoriaEtapa
from govdata.infrastructure.persistence.postgresql.models.auditoria_etapa_model import (
    AuditoriaEtapaModel,
)


def a_dominio(modelo: AuditoriaEtapaModel) -> AuditoriaEtapa:
    return AuditoriaEtapa(
        id=modelo.id, trabajo_orquestador_id=str(modelo.trabajo_orquestador_id), tipo_paso=modelo.tipo_paso,
        estado_paso=modelo.estado_paso, iniciado_en=modelo.iniciado_en, finalizado_en=modelo.finalizado_en,
        razon_omision=modelo.razon_omision, cantidad_registros=modelo.cantidad_registros, error=modelo.error,
        cache_utilizada=modelo.cache_utilizada, version_utilizada=modelo.version_utilizada,
    )


def a_modelo(etapa: AuditoriaEtapa, modelo: AuditoriaEtapaModel | None = None) -> AuditoriaEtapaModel:
    modelo = modelo or AuditoriaEtapaModel()
    if etapa.id is not None:  # pragma: no cover -- auditoria es append-only, guardar_lote solo inserta (id=None)
        modelo.id = etapa.id
    modelo.trabajo_orquestador_id = uuid.UUID(etapa.trabajo_orquestador_id)
    modelo.tipo_paso = etapa.tipo_paso
    modelo.estado_paso = etapa.estado_paso
    modelo.iniciado_en = etapa.iniciado_en
    modelo.finalizado_en = etapa.finalizado_en
    modelo.razon_omision = etapa.razon_omision
    modelo.cantidad_registros = etapa.cantidad_registros
    modelo.error = etapa.error
    modelo.cache_utilizada = etapa.cache_utilizada
    modelo.version_utilizada = etapa.version_utilizada
    return modelo
