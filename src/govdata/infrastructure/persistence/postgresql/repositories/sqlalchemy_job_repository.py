"""Adaptador: SqlAlchemyJobRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from govdata.application.ports.job_repository_port import JobRepositoryPort
from govdata.domain.entities.job import Job
from govdata.domain.entities.job_step import JobStep
from govdata.infrastructure.persistence.postgresql.mappers import job_mapper, job_step_mapper
from govdata.infrastructure.persistence.postgresql.models.job_model import JobModel
from govdata.infrastructure.persistence.postgresql.models.job_step_model import JobStepModel


class SqlAlchemyJobRepository(JobRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar(self, job: Job) -> Job:
        modelo_existente = self._session.get(JobModel, job.id)
        modelo = job_mapper.a_modelo(job, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return job_mapper.a_dominio(modelo)

    def buscar_por_id(self, job_id: uuid.UUID) -> Job | None:
        modelo = self._session.get(JobModel, job_id)
        return job_mapper.a_dominio(modelo) if modelo else None

    def registrar_step(self, step: JobStep) -> JobStep:
        modelo = job_step_mapper.a_modelo(step)
        self._session.add(modelo)
        self._session.flush()
        return job_step_mapper.a_dominio(modelo)

    def listar_steps(self, job_id: uuid.UUID) -> list[JobStep]:
        modelos = (
            self._session.execute(
                select(JobStepModel).where(JobStepModel.job_id == job_id).order_by(JobStepModel.iniciado_en.asc())
            )
            .scalars()
            .all()
        )
        return [job_step_mapper.a_dominio(m) for m in modelos]
