"""Tests: AlertaService (Submodulo 5.6)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.application.dto.estadisticas_comparacion_dto import EstadisticasComparacionDTO
from govdata.application.services.alerta_service import AlertaService
from govdata.domain.rules.reglas_configurables import ReglasCriticidad
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_cambio import TipoCambio
from tests.unit.application.fakes_modulo5 import FakeAlertaRepository

_REGLAS = ReglasCriticidad(
    umbral_score_minimo=80.0, cargos_criticos=["Director Juridico"], cargos_altos=[], campos_medios=["correo"],
    umbral_cambio_masivo_pct=30.0, umbral_cambio_masivo_absoluto=15,
)


def _stats_sin_alertas_de_documento() -> EstadisticasComparacionDTO:
    return EstadisticasComparacionDTO(
        total_funcionarios_anteriores=10, total_funcionarios_actuales=10,
        cantidad_nuevos=1, cantidad_eliminados=0, cantidad_cambios=0, cantidad_sin_cambios=9,
        porcentaje_cambios=10.0,
    )


class TestGenerarYGuardar:
    def test_genera_alerta_y_resuelve_persona_id_desde_el_mapa(self) -> None:
        repo = FakeAlertaRepository()
        servicio = AlertaService(repo, _REGLAS)
        diferencia = DiferenciaFuncionarioDTO(
            tipo_cambio=TipoCambio.FUNCIONARIO_NUEVO, fingerprint="FP1", nombre="Juan", apellido="Perez",
            cargo="Director Juridico", dependencia="Legal", correo=None, telefono=None, area="juridica",
            criticidad=NivelCriticidad.CRITICO,
        )
        alertas = servicio.generar_y_guardar(
            [diferencia], _stats_sin_alertas_de_documento(), entidad_id=1, documento_id=10,
            persona_id_por_fingerprint={"FP1": 42}, detectado_en=datetime.now(UTC),
        )
        assert len(alertas) == 1
        assert alertas[0].persona_id == 42
        assert len(repo.guardadas) == 1

    def test_sin_cambios_no_genera_alertas(self) -> None:
        repo = FakeAlertaRepository()
        servicio = AlertaService(repo, _REGLAS)
        diferencia = DiferenciaFuncionarioDTO(
            tipo_cambio=TipoCambio.SIN_CAMBIOS, fingerprint="FP1", nombre="Juan", apellido="Perez",
            cargo="Chofer", dependencia="X", correo=None, telefono=None, area="juridica",
        )
        alertas = servicio.generar_y_guardar(
            [diferencia], _stats_sin_alertas_de_documento(), 1, 10, {}, datetime.now(UTC)
        )
        assert alertas == []

    def test_persona_id_ausente_en_el_mapa_queda_none(self) -> None:
        repo = FakeAlertaRepository()
        servicio = AlertaService(repo, _REGLAS)
        diferencia = DiferenciaFuncionarioDTO(
            tipo_cambio=TipoCambio.FUNCIONARIO_ELIMINADO, fingerprint="FPX", nombre="Juan", apellido="Perez",
            cargo="Director Juridico", dependencia="Legal", correo=None, telefono=None, area="juridica",
            criticidad=NivelCriticidad.CRITICO,
        )
        alertas = servicio.generar_y_guardar(
            [diferencia], _stats_sin_alertas_de_documento(), 1, 10, {}, datetime.now(UTC)
        )
        assert alertas[0].persona_id is None
