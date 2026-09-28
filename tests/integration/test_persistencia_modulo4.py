"""Tests de integracion de persistencia -- piezas del Modulo 4 que los
tests end-to-end (`test_extraccion_real.py`) no ejercitan directamente:
`SqlAlchemyJobRepository` (+ `job_mapper`/`job_step_mapper`),
`SqlAlchemyPersonaRepository.buscar_por_fingerprint_hash`, y
`SqlAlchemyFuncionarioRepository.buscar_con_filtros`/`buscar_vigente`
(Submodulo 4.7 -- consulta por filtros) contra SQLite real.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from govdata.application.dto.filtros_consulta_dto import FiltrosConsultaDTO
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.job import Job, JobStatus, TipoJob
from govdata.domain.entities.job_step import JobStep
from govdata.domain.entities.persona import Persona
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.cargo import Cargo
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.telefono import Telefono
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_funcionario_repository import (
    SqlAlchemyFuncionarioRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_job_repository import (
    SqlAlchemyJobRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)


class TestSqlAlchemyJobRepository:
    def test_guardar_y_buscar_por_id(self, sesion) -> None:
        repo = SqlAlchemyJobRepository(sesion)
        job = Job(tipo=TipoJob.CONSULTA_INDIVIDUAL, entidad_id=1, fecha_inicio=datetime.now(UTC))

        guardado = repo.guardar(job)
        sesion.flush()

        recuperado = repo.buscar_por_id(guardado.id)
        assert recuperado is not None
        assert recuperado.id == job.id
        assert recuperado.tipo == TipoJob.CONSULTA_INDIVIDUAL
        assert recuperado.estado == JobStatus.PENDIENTE

    def test_buscar_por_id_inexistente_devuelve_none(self, sesion) -> None:
        repo = SqlAlchemyJobRepository(sesion)
        assert repo.buscar_por_id(uuid.uuid4()) is None

    def test_actualizar_job_existente_no_duplica_fila(self, sesion) -> None:
        repo = SqlAlchemyJobRepository(sesion)
        job = Job(tipo=TipoJob.CONSULTA_MASIVA, fecha_inicio=datetime.now(UTC))
        repo.guardar(job)

        job.transicionar(JobStatus.DESCUBRIENDO)
        repo.guardar(job)
        sesion.flush()

        recuperado = repo.buscar_por_id(job.id)
        assert recuperado is not None
        assert recuperado.estado == JobStatus.DESCUBRIENDO

    def test_registrar_step_y_listar_steps_en_orden(self, sesion) -> None:
        repo = SqlAlchemyJobRepository(sesion)
        job = Job(tipo=TipoJob.CONSULTA_FILTROS, fecha_inicio=datetime.now(UTC))
        repo.guardar(job)
        sesion.flush()

        repo.registrar_step(JobStep(job_id=job.id, estado=JobStatus.DESCUBRIENDO, iniciado_en=datetime.now(UTC)))
        repo.registrar_step(JobStep(job_id=job.id, estado=JobStatus.EXTRAYENDO, iniciado_en=datetime.now(UTC)))
        sesion.flush()

        steps = repo.listar_steps(job.id)
        assert len(steps) == 2
        assert steps[0].estado == JobStatus.DESCUBRIENDO
        assert steps[1].estado == JobStatus.EXTRAYENDO

    def test_listar_steps_de_job_sin_steps_es_vacio(self, sesion) -> None:
        repo = SqlAlchemyJobRepository(sesion)
        job = Job(tipo=TipoJob.CONSULTA_INDIVIDUAL, fecha_inicio=datetime.now(UTC))
        repo.guardar(job)
        sesion.flush()
        assert repo.listar_steps(job.id) == []


class TestSqlAlchemyPersonaRepositoryFingerprint:
    def test_buscar_por_fingerprint_hash_encuentra_persona_existente(self, sesion) -> None:
        repo = SqlAlchemyPersonaRepository(sesion)
        persona = Persona(
            nombre_completo=NombreCompleto(nombres="Juan", apellidos="Perez"),
            fingerprint="JUANPEREZ",
            fingerprint_hash="hash-abc-123",
        )
        repo.guardar(persona)
        sesion.flush()

        encontrada = repo.buscar_por_fingerprint_hash("hash-abc-123")
        assert encontrada is not None
        assert encontrada.fingerprint == "JUANPEREZ"

    def test_buscar_por_fingerprint_hash_inexistente_devuelve_none(self, sesion) -> None:
        repo = SqlAlchemyPersonaRepository(sesion)
        assert repo.buscar_por_fingerprint_hash("no-existe") is None

    def test_buscar_por_id(self, sesion) -> None:
        repo = SqlAlchemyPersonaRepository(sesion)
        persona = repo.guardar(Persona(nombre_completo=NombreCompleto(nombres="Ana", apellidos="Ruiz")))
        sesion.flush()
        assert repo.buscar_por_id(persona.id).nombre_completo.nombres == "ANA"
        assert repo.buscar_por_id(999_999) is None

    def test_buscar_por_cedula(self, sesion) -> None:
        repo = SqlAlchemyPersonaRepository(sesion)
        repo.guardar(Persona(nombre_completo=NombreCompleto(nombres="Ana", apellidos="Ruiz"), cedula="1234567890"))
        sesion.flush()
        assert repo.buscar_por_cedula("1234567890") is not None
        assert repo.buscar_por_cedula("0000000000") is None

    def test_buscar_candidatas_por_nombre(self, sesion) -> None:
        repo = SqlAlchemyPersonaRepository(sesion)
        nombre = NombreCompleto(nombres="Ana", apellidos="Ruiz")
        repo.guardar(Persona(nombre_completo=nombre))
        sesion.flush()
        assert len(repo.buscar_candidatas_por_nombre(nombre)) == 1
        assert repo.buscar_candidatas_por_nombre(NombreCompleto(nombres="Nadie", apellidos="Aqui")) == []

    def test_guardar_persona_existente_actualiza_en_vez_de_duplicar(self, sesion) -> None:
        repo = SqlAlchemyPersonaRepository(sesion)
        persona = repo.guardar(Persona(nombre_completo=NombreCompleto(nombres="Ana", apellidos="Ruiz")))
        sesion.flush()

        persona.cedula = "1234567890"
        repo.guardar(persona)
        sesion.flush()

        recuperada = repo.buscar_por_id(persona.id)
        assert recuperada.cedula == "1234567890"


def _persona(sesion, correo: str | None, telefono: str | None, sufijo: str) -> Persona:
    repo = SqlAlchemyPersonaRepository(sesion)
    return repo.guardar(
        Persona(
            nombre_completo=NombreCompleto(nombres=f"Nombre{sufijo}", apellidos=f"Apellido{sufijo}"),
            correo=Correo.crear_opcional(correo),
            telefono=Telefono.crear_opcional(telefono),
            fingerprint=f"FP{sufijo}",
            fingerprint_hash=f"fp-hash-{sufijo}",
        )
    )


def _entidad(sesion, nombre: str, tipo_institucion: str | None = None) -> EntidadModel:
    modelo = EntidadModel(
        nombre=nombre,
        url_transparencia=f"https://x/{nombre}",
        portal_origen="dpe",
        metadata_extra={"tipo_institucion": tipo_institucion} if tipo_institucion else {},
    )
    sesion.add(modelo)
    sesion.flush()
    return modelo


class TestSqlAlchemyFuncionarioRepositoryFiltros:
    def _preparar_escenario(self, sesion):
        """3 funcionarios: (1) juridica, con correo y telefono, en un
        Ministerio; (2) financiera, sin correo, en una Universidad; (3)
        juridica, sin telefono, en el mismo Ministerio que (1)."""
        func_repo = SqlAlchemyFuncionarioRepository(sesion)

        ministerio = _entidad(sesion, "Ministerio X", tipo_institucion="Ministerios")
        universidad = _entidad(sesion, "Universidad Y", tipo_institucion="Universidades")

        p1 = _persona(sesion, "p1@x.gob.ec", "0991111111", "1")
        p2 = _persona(sesion, None, "0992222222", "2")
        p3 = _persona(sesion, "p3@x.gob.ec", None, "3")

        f1 = func_repo.guardar(
            Funcionario(
                persona_id=p1.id, entidad_id=ministerio.id, cargo=Cargo("Director Juridico"),
                dependencia="Legal", area_clasificada=AreaRelevante.JURIDICA,
            )
        )
        f2 = func_repo.guardar(
            Funcionario(
                persona_id=p2.id, entidad_id=universidad.id, cargo=Cargo("Director Financiero"),
                dependencia="Finanzas", area_clasificada=AreaRelevante.FINANCIERA,
            )
        )
        f3 = func_repo.guardar(
            Funcionario(
                persona_id=p3.id, entidad_id=ministerio.id, cargo=Cargo("Asesor Juridico"),
                dependencia="Legal", area_clasificada=AreaRelevante.JURIDICA,
            )
        )
        sesion.flush()
        return func_repo, ministerio, universidad, (f1, f2, f3)

    def test_filtra_por_area(self, sesion) -> None:
        func_repo, *_ = self._preparar_escenario(sesion)
        resultado = func_repo.buscar_con_filtros(FiltrosConsultaDTO(area=AreaRelevante.JURIDICA))
        assert len(resultado) == 2
        assert all(f.area_clasificada == AreaRelevante.JURIDICA for f in resultado)

    def test_filtra_por_cargo_contiene_insensible_a_mayusculas(self, sesion) -> None:
        func_repo, *_ = self._preparar_escenario(sesion)
        resultado = func_repo.buscar_con_filtros(FiltrosConsultaDTO(cargo_contiene="director"))
        assert len(resultado) == 2
        assert {str(f.cargo) for f in resultado} == {"Director Juridico", "Director Financiero"}

    def test_filtra_por_correo_disponible(self, sesion) -> None:
        func_repo, *_ = self._preparar_escenario(sesion)
        resultado = func_repo.buscar_con_filtros(FiltrosConsultaDTO(correo_disponible=True))
        assert len(resultado) == 2

        sin_correo = func_repo.buscar_con_filtros(FiltrosConsultaDTO(correo_disponible=False))
        assert len(sin_correo) == 1

    def test_filtra_por_telefono_disponible(self, sesion) -> None:
        func_repo, *_ = self._preparar_escenario(sesion)
        resultado = func_repo.buscar_con_filtros(FiltrosConsultaDTO(telefono_disponible=True))
        assert len(resultado) == 2

        sin_telefono = func_repo.buscar_con_filtros(FiltrosConsultaDTO(telefono_disponible=False))
        assert len(sin_telefono) == 1

    def test_filtra_por_tipo_institucion(self, sesion) -> None:
        func_repo, ministerio, _universidad, _ = self._preparar_escenario(sesion)
        resultado = func_repo.buscar_con_filtros(FiltrosConsultaDTO(tipo_institucion="Ministerios"))
        assert len(resultado) == 2
        assert all(f.entidad_id == ministerio.id for f in resultado)

    def test_combina_multiples_filtros(self, sesion) -> None:
        func_repo, ministerio, _, _ = self._preparar_escenario(sesion)
        resultado = func_repo.buscar_con_filtros(
            FiltrosConsultaDTO(area=AreaRelevante.JURIDICA, correo_disponible=True, tipo_institucion="Ministerios")
        )
        # f1 y f3 son ambos juridica + con correo + en el Ministerio;
        # f2 (financiera, sin correo, en la Universidad) queda excluido.
        assert len(resultado) == 2
        assert all(f.entidad_id == ministerio.id for f in resultado)

    def test_sin_filtros_devuelve_todos(self, sesion) -> None:
        func_repo, *_ = self._preparar_escenario(sesion)
        resultado = func_repo.buscar_con_filtros(FiltrosConsultaDTO())
        assert len(resultado) == 3

    def test_buscar_vigente_encuentra_solo_sin_fecha_fin(self, sesion) -> None:
        func_repo, ministerio, _, (f1, _, _) = self._preparar_escenario(sesion)
        vigente = func_repo.buscar_vigente(f1.persona_id, ministerio.id)
        assert vigente is not None
        assert vigente.id == f1.id

    def test_buscar_vigente_sin_coincidencia_devuelve_none(self, sesion) -> None:
        func_repo, *_ = self._preparar_escenario(sesion)
        assert func_repo.buscar_vigente(999, 999) is None

    def test_listar_por_entidad_solo_vigentes_por_defecto(self, sesion) -> None:
        func_repo, ministerio, _, (f1, _, f3) = self._preparar_escenario(sesion)
        f1.fecha_fin = date(2026, 1, 1)
        func_repo.guardar(f1)
        sesion.flush()

        vigentes = func_repo.listar_por_entidad(ministerio.id)
        assert {f.id for f in vigentes} == {f3.id}

        todos = func_repo.listar_por_entidad(ministerio.id, solo_vigentes=False)
        assert {f.id for f in todos} == {f1.id, f3.id}

    def test_guardar_funcionario_existente_actualiza_en_vez_de_duplicar(self, sesion) -> None:
        func_repo, ministerio, _, (f1, *_) = self._preparar_escenario(sesion)
        f1.dependencia = "Legal Actualizado"
        func_repo.guardar(f1)
        sesion.flush()

        recuperado = func_repo.buscar_vigente(f1.persona_id, ministerio.id)
        assert recuperado.dependencia == "Legal Actualizado"
