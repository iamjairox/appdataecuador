"""Tests: ComparacionForoService."""

from __future__ import annotations

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.services.comparacion_foro_service import ComparacionForoService
from govdata.domain.entities.registro_foro import RegistroForo
from govdata.domain.value_objects.estado_registro_foro import EstadoRegistroForo
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo
from tests.unit.application.fakes_modulo8 import FakeRegistroForoRepository


class TestComparacionForoService:
    def test_compara_contra_vigentes_persistidos(self) -> None:
        repo = FakeRegistroForoRepository()
        repo.guardar(
            RegistroForo(
                persona_master_id=1, clave_registro="registro:r1", registro="R1", provincia="Pichincha",
                estado=EstadoRegistroForo.VIGENTE,
            )
        )
        servicio = ComparacionForoService(repo)
        actuales = [RegistroForoDTO(registro="R1", provincia="Pichincha", estado="vigente")]
        diffs = servicio.comparar(1, actuales)
        assert len(diffs) == 1
        assert diffs[0].tipo_cambio == TipoCambioForo.SIN_CAMBIOS

    def test_sin_vigentes_persistidos_todo_es_nuevo(self) -> None:
        repo = FakeRegistroForoRepository()
        servicio = ComparacionForoService(repo)
        diffs = servicio.comparar(1, [RegistroForoDTO(registro="R1")])
        assert diffs[0].tipo_cambio == TipoCambioForo.DATO_NUEVO
