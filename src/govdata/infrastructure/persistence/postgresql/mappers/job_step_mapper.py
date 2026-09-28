"""Mapper: JobStepModel <-> JobStep (dominio)."""

from __future__ import annotations

from govdata.domain.entities.job_step import JobStep
from govdata.infrastructure.persistence.postgresql.models.job_step_model import JobStepModel


def a_dominio(modelo: JobStepModel) -> JobStep:
    return JobStep(
        id=modelo.id,
        job_id=modelo.job_id,
        estado=modelo.estado,
        iniciado_en=modelo.iniciado_en,
        finalizado_en=modelo.finalizado_en,
        mensaje=modelo.mensaje,
    )


def a_modelo(step: JobStep) -> JobStepModel:
    return JobStepModel(
        id=step.id,
        job_id=step.job_id,
        estado=step.estado,
        iniciado_en=step.iniciado_en,
        finalizado_en=step.finalizado_en,
        mensaje=step.mensaje,
    )
