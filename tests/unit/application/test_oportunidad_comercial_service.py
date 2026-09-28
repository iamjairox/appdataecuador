"""Tests: OportunidadComercialService (Submodulo 5.17)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.application.dto.estadisticas_comparacion_dto import EstadisticasComparacionDTO
from govdata.application.services.oportunidad_comercial_service import OportunidadComercialService
from govdata.domain.entities.oportunidad_comercial import TipoOportunidad
from govdata.domain.rules.reglas_configurables import ReglasCriticidad
from govdata.domain.value_objects.tipo_cambio import TipoCambio
from tests.unit.application.fakes_modulo5 import FakeOportunidadComercialRepository

_REGLAS = ReglasCriticidad(
    umbral_score_minimo=80.0, cargos_criticos=[], cargos_altos=[], campos_medios=[],
    umbral_cambio_masivo_pct=30.0, umbral_cambio_masivo_absoluto=15,
)


def _stats_normal() -> EstadisticasComparacionDTO:
    return EstadisticasComparacionDTO(
        total_funcionarios_anteriores=10, total_funcionarios_actuales=10,
        cantidad_nuevos=1, cantidad_eliminados=0, cantidad_cambios=0, cantidad_sin_cambios=9,
        porcentaje_cambios=10.0,
    )


def test_genera_y_guarda_oportunidad_con_persona_id_resuelta() -> None:
    repo = FakeOportunidadComercialRepository()
    servicio = OportunidadComercialService(repo, _REGLAS)
    diferencia = DiferenciaFuncionarioDTO(
        tipo_cambio=TipoCambio.FUNCIONARIO_NUEVO, fingerprint="FP1", nombre="Juan", apellido="Perez",
        cargo="Director Juridico", dependencia="Legal", correo=None, telefono=None, area="juridica",
    )
    oportunidades = servicio.generar_y_guardar(
        [diferencia], _stats_normal(), entidad_id=1, persona_id_por_fingerprint={"FP1": 7}, detectado_en=datetime.now(UTC)
    )
    assert len(oportunidades) == 1
    assert oportunidades[0].tipo == TipoOportunidad.NUEVO_DIRECTOR_JURIDICO
    assert oportunidades[0].persona_id == 7
    assert len(repo.guardadas) == 1


def test_sin_patrones_relevantes_no_guarda_nada() -> None:
    repo = FakeOportunidadComercialRepository()
    servicio = OportunidadComercialService(repo, _REGLAS)
    diferencia = DiferenciaFuncionarioDTO(
        tipo_cambio=TipoCambio.FUNCIONARIO_NUEVO, fingerprint="FP1", nombre="Juan", apellido="Perez",
        cargo="Chofer", dependencia="X", correo=None, telefono=None, area="juridica",
    )
    oportunidades = servicio.generar_y_guardar([diferencia], _stats_normal(), 1, {}, datetime.now(UTC))
    assert oportunidades == []
