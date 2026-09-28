"""Tests: invariantes de validacion de entidades de dominio reutilizadas
intensivamente por el Modulo 4 (`Funcionario`, `Persona`, `JobStep`) y de
`Entidad` que aun no tenian cobertura de sus ramas de error."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest

from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.job import JobStatus
from govdata.domain.entities.job_step import JobStep
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import (
    EntidadInvalidaError,
    FuncionarioInvalidoError,
    PersonaInvalidaError,
)
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.cargo import Cargo
from govdata.domain.value_objects.nombre_completo import NombreCompleto


class TestEntidadValidacion:
    def test_url_transparencia_vacia_lanza_error(self) -> None:
        with pytest.raises(EntidadInvalidaError, match="url_transparencia"):
            Entidad(nombre="X", url_transparencia="   ", portal_origen="dpe")

    def test_portal_origen_vacio_lanza_error(self) -> None:
        with pytest.raises(EntidadInvalidaError, match="portal_origen"):
            Entidad(nombre="X", url_transparencia="https://x", portal_origen="")


class TestFuncionarioValidacion:
    def test_persona_id_none_lanza_error(self) -> None:
        with pytest.raises(FuncionarioInvalidoError, match="persona_id"):
            Funcionario(
                persona_id=None,  # type: ignore[arg-type]
                entidad_id=1,
                cargo=Cargo("Director Juridico"),
                dependencia="X",
                area_clasificada=AreaRelevante.JURIDICA,
            )

    def test_entidad_id_none_lanza_error(self) -> None:
        with pytest.raises(FuncionarioInvalidoError, match="entidad_id"):
            Funcionario(
                persona_id=1,
                entidad_id=None,  # type: ignore[arg-type]
                cargo=Cargo("Director Juridico"),
                dependencia="X",
                area_clasificada=AreaRelevante.JURIDICA,
            )

    def test_dependencia_vacia_lanza_error(self) -> None:
        with pytest.raises(FuncionarioInvalidoError, match="dependencia"):
            Funcionario(
                persona_id=1, entidad_id=1, cargo=Cargo("Director Juridico"),
                dependencia="   ", area_clasificada=AreaRelevante.JURIDICA,
            )

    def test_score_fuera_de_rango_lanza_error(self) -> None:
        with pytest.raises(FuncionarioInvalidoError, match="score_clasificacion"):
            Funcionario(
                persona_id=1, entidad_id=1, cargo=Cargo("Director Juridico"),
                dependencia="X", area_clasificada=AreaRelevante.JURIDICA,
                score_clasificacion=150.0,
            )

    def test_finalizar_antes_de_fecha_inicio_lanza_error(self) -> None:
        funcionario = Funcionario(
            persona_id=1, entidad_id=1, cargo=Cargo("Director Juridico"), dependencia="X",
            area_clasificada=AreaRelevante.JURIDICA, fecha_inicio=date(2026, 6, 1),
        )
        with pytest.raises(FuncionarioInvalidoError, match="fecha_inicio"):
            funcionario.finalizar(date(2026, 1, 1))

    def test_finalizar_valido_marca_no_vigente(self) -> None:
        funcionario = Funcionario(
            persona_id=1, entidad_id=1, cargo=Cargo("Director Juridico"), dependencia="X",
            area_clasificada=AreaRelevante.JURIDICA, fecha_inicio=date(2026, 1, 1),
        )
        assert funcionario.vigente is True
        funcionario.finalizar(date(2026, 6, 1))
        assert funcionario.vigente is False


class TestPersonaValidacionCedula:
    def test_cedula_con_digitos_se_acepta(self) -> None:
        persona = Persona(nombre_completo=NombreCompleto(nombres="Juan", apellidos="Perez"), cedula="1234567890")
        assert persona.cedula == "1234567890"

    def test_cedula_no_numerica_lanza_error(self) -> None:
        with pytest.raises(PersonaInvalidaError, match="Cedula invalida"):
            Persona(nombre_completo=NombreCompleto(nombres="Juan", apellidos="Perez"), cedula="ABC123")

    def test_cedula_solo_espacios_se_normaliza_a_none(self) -> None:
        persona = Persona(nombre_completo=NombreCompleto(nombres="Juan", apellidos="Perez"), cedula="   ")
        assert persona.cedula is None


class TestJobStepDuracion:
    def test_duracion_segundos_es_none_sin_finalizar(self) -> None:
        step = JobStep(job_id=uuid.uuid4(), estado=JobStatus.DESCUBRIENDO, iniciado_en=datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC))
        assert step.duracion_segundos is None
