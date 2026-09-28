"""Mapper: AuditoriaComparacionModel <-> AuditoriaComparacion (dominio)."""

from __future__ import annotations

from govdata.domain.entities.auditoria_comparacion import AuditoriaComparacion
from govdata.infrastructure.persistence.postgresql.models.auditoria_comparacion_model import (
    AuditoriaComparacionModel,
)


def a_dominio(modelo: AuditoriaComparacionModel) -> AuditoriaComparacion:
    return AuditoriaComparacion(
        id=modelo.id,
        entidad_id=modelo.entidad_id,
        documento_id=modelo.documento_id,
        version_documento=modelo.version_documento,
        ejecutado_por=modelo.ejecutado_por,
        iniciado_en=modelo.iniciado_en,
        finalizado_en=modelo.finalizado_en,
        duracion_segundos=modelo.duracion_segundos,
        cambios_detectados=modelo.cambios_detectados,
        errores=list(modelo.errores or []),
    )


def a_modelo(
    auditoria: AuditoriaComparacion, modelo: AuditoriaComparacionModel | None = None
) -> AuditoriaComparacionModel:
    modelo = modelo or AuditoriaComparacionModel()
    modelo.id = auditoria.id  # type: ignore[assignment]
    modelo.entidad_id = auditoria.entidad_id
    modelo.documento_id = auditoria.documento_id
    modelo.version_documento = auditoria.version_documento
    modelo.ejecutado_por = auditoria.ejecutado_por
    modelo.iniciado_en = auditoria.iniciado_en
    modelo.finalizado_en = auditoria.finalizado_en
    modelo.duracion_segundos = auditoria.duracion_segundos
    modelo.cambios_detectados = auditoria.cambios_detectados
    modelo.errores = list(auditoria.errores)
    return modelo
