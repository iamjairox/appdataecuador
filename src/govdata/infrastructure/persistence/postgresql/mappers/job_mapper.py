"""Mapper: JobModel <-> Job (dominio)."""

from __future__ import annotations

from govdata.domain.entities.job import Job
from govdata.infrastructure.persistence.postgresql.models.job_model import JobModel


def a_dominio(modelo: JobModel) -> Job:
    return Job(
        id=modelo.id,
        tipo=modelo.tipo,
        entidad_id=modelo.entidad_id,
        estado=modelo.estado,
        porcentaje=modelo.porcentaje,
        fecha_inicio=modelo.fecha_inicio,
        fecha_fin=modelo.fecha_fin,
        errores=list(modelo.errores or []),
        reintentos=modelo.reintentos,
    )


def a_modelo(job: Job, modelo: JobModel | None = None) -> JobModel:
    modelo = modelo or JobModel()
    modelo.id = job.id
    modelo.tipo = job.tipo
    modelo.entidad_id = job.entidad_id
    modelo.estado = job.estado
    modelo.porcentaje = job.porcentaje
    modelo.fecha_inicio = job.fecha_inicio
    modelo.fecha_fin = job.fecha_fin
    modelo.errores = list(job.errores)
    modelo.reintentos = job.reintentos
    return modelo
