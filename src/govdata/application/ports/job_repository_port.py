"""Puerto: JobRepositoryPort."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from govdata.domain.entities.job import Job
from govdata.domain.entities.job_step import JobStep


class JobRepositoryPort(ABC):
    """Persistencia de Jobs y su historial de JobStep."""

    @abstractmethod
    def guardar(self, job: Job) -> Job: ...

    @abstractmethod
    def buscar_por_id(self, job_id: uuid.UUID) -> Job | None: ...

    @abstractmethod
    def registrar_step(self, step: JobStep) -> JobStep: ...

    @abstractmethod
    def listar_steps(self, job_id: uuid.UUID) -> list[JobStep]: ...
