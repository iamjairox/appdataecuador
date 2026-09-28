"""Tests: ComparacionAcademicaService."""

from __future__ import annotations

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.application.services.comparacion_academica_service import ComparacionAcademicaService
from govdata.domain.entities.titulo_academico import TituloAcademico
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico
from tests.unit.application.fakes_modulo7 import FakeTituloAcademicoRepository


class TestComparar:
    def test_sin_titulos_previos_todo_es_nuevo(self) -> None:
        repo = FakeTituloAcademicoRepository()
        servicio = ComparacionAcademicaService(repo)
        actuales = [PersonaAcademicaDTO(titulo="ABOGADO", nivel="TERCER NIVEL", institucion="UCE", numero_registro="R1")]
        diffs = servicio.comparar(1, actuales)
        assert diffs[0].tipo_cambio == TipoCambioAcademico.TITULO_NUEVO

    def test_compara_contra_vigentes_persistidos(self) -> None:
        from govdata.domain.value_objects.estado_registro_academico import EstadoRegistroAcademico

        repo = FakeTituloAcademicoRepository()
        repo.guardar(
            TituloAcademico(
                persona_master_id=1, clave_titulo="registro:r1", titulo="ABOGADO", nivel="TERCER NIVEL",
                institucion="UCE", numero_registro="R1", estado=EstadoRegistroAcademico.VIGENTE,
            )
        )
        servicio = ComparacionAcademicaService(repo)
        actuales = [
            PersonaAcademicaDTO(
                titulo="ABOGADO", nivel="TERCER NIVEL", institucion="UCE", numero_registro="R1", estado="vigente"
            )
        ]
        diffs = servicio.comparar(1, actuales)
        assert diffs[0].tipo_cambio == TipoCambioAcademico.SIN_CAMBIOS

    def test_solo_compara_contra_titulos_de_esa_persona_master(self) -> None:
        repo = FakeTituloAcademicoRepository()
        repo.guardar(
            TituloAcademico(
                persona_master_id=99, clave_titulo="registro:r1", titulo="ABOGADO", nivel="TERCER NIVEL",
                institucion="UCE", numero_registro="R1",
            )
        )
        servicio = ComparacionAcademicaService(repo)
        actuales = [PersonaAcademicaDTO(titulo="ABOGADO", nivel="TERCER NIVEL", institucion="UCE", numero_registro="R1")]
        diffs = servicio.comparar(1, actuales)
        assert diffs[0].tipo_cambio == TipoCambioAcademico.TITULO_NUEVO
