"""Dobles de prueba (fakes) de los puertos del Modulo 4."""

from __future__ import annotations

import uuid

from govdata.application.dto.filtros_consulta_dto import FiltrosConsultaDTO
from govdata.application.dto.resultado_descubrimiento_dto import ResultadoDescubrimientoEntidadDTO
from govdata.application.dto.resultado_unificado_dto import ResultadoUnificadoDTO
from govdata.application.ports.descarga_port import DescargaPort
from govdata.application.ports.descubrimiento_port import DescubrimientoPort
from govdata.application.ports.extraccion_port import ExtraccionPort
from govdata.application.ports.funcionario_repository_port import FuncionarioRepositoryPort
from govdata.application.ports.job_repository_port import JobRepositoryPort
from govdata.application.ports.persona_repository_port import PersonaRepositoryPort
from govdata.domain.entities.documento import DocumentoTransparencia
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.job import Job
from govdata.domain.entities.job_step import JobStep
from govdata.domain.entities.persona import Persona
from govdata.domain.value_objects.nombre_completo import NombreCompleto


class FakePersonaRepository(PersonaRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardadas: list[Persona] = []

    def guardar(self, persona: Persona) -> Persona:
        if persona.id is None:
            persona.id = self._siguiente_id
            self._siguiente_id += 1
            self.guardadas.append(persona)
        return persona

    def buscar_por_id(self, persona_id: int) -> Persona | None:
        return next((p for p in self.guardadas if p.id == persona_id), None)

    def buscar_por_cedula(self, cedula: str) -> Persona | None:
        return next((p for p in self.guardadas if p.cedula == cedula), None)

    def buscar_candidatas_por_nombre(self, nombre: NombreCompleto) -> list[Persona]:
        return [p for p in self.guardadas if p.nombre_completo == nombre]

    def buscar_por_fingerprint_hash(self, fingerprint_hash: str) -> Persona | None:
        return next((p for p in self.guardadas if p.fingerprint_hash == fingerprint_hash), None)


class FakeFuncionarioRepositoryExtraccion(FuncionarioRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardados: list[Funcionario] = []

    def guardar(self, funcionario: Funcionario) -> Funcionario:
        if funcionario.id is None:
            funcionario.id = self._siguiente_id
            self._siguiente_id += 1
            self.guardados.append(funcionario)
        return funcionario

    def guardar_lote(self, funcionarios: list[Funcionario]) -> list[Funcionario]:
        return [self.guardar(f) for f in funcionarios]

    def buscar_vigente(self, persona_id: int, entidad_id: int) -> Funcionario | None:
        return next(
            (
                f
                for f in self.guardados
                if f.persona_id == persona_id and f.entidad_id == entidad_id and f.fecha_fin is None
            ),
            None,
        )

    def listar_por_entidad(self, entidad_id: int, solo_vigentes: bool = True) -> list[Funcionario]:
        return [
            f
            for f in self.guardados
            if f.entidad_id == entidad_id and (not solo_vigentes or f.fecha_fin is None)
        ]

    def listar_por_documento(self, documento_id: int) -> list[Funcionario]:
        return [f for f in self.guardados if f.documento_id == documento_id]

    def buscar_con_filtros(self, filtros: FiltrosConsultaDTO) -> list[Funcionario]:
        resultado = list(self.guardados)
        if filtros.area is not None:
            resultado = [f for f in resultado if f.area_clasificada == filtros.area]
        if filtros.cargo_contiene:
            resultado = [f for f in resultado if filtros.cargo_contiene.lower() in str(f.cargo).lower()]
        return resultado


class FakeJobRepository(JobRepositoryPort):
    def __init__(self) -> None:
        self.jobs: dict[uuid.UUID, Job] = {}
        self.steps: list[JobStep] = []

    def guardar(self, job: Job) -> Job:
        self.jobs[job.id] = job
        return job

    def buscar_por_id(self, job_id: uuid.UUID) -> Job | None:
        return self.jobs.get(job_id)

    def registrar_step(self, step: JobStep) -> JobStep:
        step.id = len(self.steps) + 1
        self.steps.append(step)
        return step

    def listar_steps(self, job_id: uuid.UUID) -> list[JobStep]:
        return [s for s in self.steps if s.job_id == job_id]


class FakeDescubrimientoPort(DescubrimientoPort):
    def __init__(self, resultado: ResultadoDescubrimientoEntidadDTO) -> None:
        self._resultado = resultado
        self.llamadas = 0

    def descubrir(self, entidad):  # type: ignore[no-untyped-def]
        self.llamadas += 1
        return self._resultado


class FakeDescargaPort(DescargaPort):
    def __init__(self, documento_resultado: DocumentoTransparencia | None = None, error: Exception | None = None) -> None:
        self._documento_resultado = documento_resultado
        self._error = error
        self.llamadas = 0

    def descargar(self, documento: DocumentoTransparencia) -> DocumentoTransparencia:
        self.llamadas += 1
        if self._error:
            raise self._error
        return self._documento_resultado or documento


class FakeExtraccionPort(ExtraccionPort):
    def __init__(self, resultado: ResultadoUnificadoDTO) -> None:
        self._resultado = resultado
        self.llamadas = 0

    def extraer(self, entidad, documento, mes_publicado) -> ResultadoUnificadoDTO:  # type: ignore[no-untyped-def]
        self.llamadas += 1
        return self._resultado
