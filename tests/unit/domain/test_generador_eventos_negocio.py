"""Tests: Generador de Oportunidades Comerciales (Submodulo 5.17)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.diferencia_dto import CampoModificadoDTO, DiferenciaFuncionarioDTO
from govdata.application.dto.estadisticas_comparacion_dto import EstadisticasComparacionDTO
from govdata.domain.entities.oportunidad_comercial import TipoOportunidad
from govdata.domain.rules.generador_eventos_negocio import (
    generar_oportunidades_documento,
    generar_oportunidades_funcionario,
)
from govdata.domain.rules.reglas_configurables import ReglasCriticidad
from govdata.domain.value_objects.tipo_cambio import TipoCambio

_AHORA = datetime(2026, 7, 1, tzinfo=UTC)
_REGLAS = ReglasCriticidad(
    umbral_score_minimo=80.0, cargos_criticos=[], cargos_altos=[], campos_medios=[],
    umbral_cambio_masivo_pct=30.0, umbral_cambio_masivo_absoluto=15,
)


def _diferencia(tipo: TipoCambio, cargo: str, campos: tuple = ()) -> DiferenciaFuncionarioDTO:
    return DiferenciaFuncionarioDTO(
        tipo_cambio=tipo, fingerprint="X", nombre="Juan", apellido="Perez", cargo=cargo,
        dependencia="Dep", correo=None, telefono=None, area="juridica", campos_modificados=campos,
    )


class TestOportunidadesPorContratacionExterna:
    def test_nuevo_director_juridico(self) -> None:
        d = _diferencia(TipoCambio.FUNCIONARIO_NUEVO, "Director Juridico")
        oportunidades = generar_oportunidades_funcionario(d, entidad_id=1, persona_id=5, detectado_en=_AHORA)
        assert any(o.tipo == TipoOportunidad.NUEVO_DIRECTOR_JURIDICO for o in oportunidades)
        assert oportunidades[0].persona_id == 5

    def test_nuevo_procurador(self) -> None:
        d = _diferencia(TipoCambio.FUNCIONARIO_NUEVO, "Procurador")
        oportunidades = generar_oportunidades_funcionario(d, 1, 5, _AHORA)
        assert any(o.tipo == TipoOportunidad.NUEVO_PROCURADOR for o in oportunidades)

    def test_nuevo_director_financiero(self) -> None:
        d = _diferencia(TipoCambio.FUNCIONARIO_NUEVO, "Director Financiero")
        oportunidades = generar_oportunidades_funcionario(d, 1, 5, _AHORA)
        assert any(o.tipo == TipoOportunidad.NUEVO_DIRECTOR_FINANCIERO for o in oportunidades)

    def test_cargo_no_relevante_no_genera_oportunidad(self) -> None:
        d = _diferencia(TipoCambio.FUNCIONARIO_NUEVO, "Chofer")
        assert generar_oportunidades_funcionario(d, 1, 5, _AHORA) == []


class TestCambioMaximaAutoridadJuridica:
    def test_ascenso_interno_hacia_director_juridico(self) -> None:
        d = _diferencia(
            TipoCambio.CAMBIO_CARGO, "Director Juridico",
            campos=(CampoModificadoDTO("cargo", "Asesor Juridico", "Director Juridico"),),
        )
        oportunidades = generar_oportunidades_funcionario(d, 1, 5, _AHORA)
        assert any(o.tipo == TipoOportunidad.CAMBIO_MAXIMA_AUTORIDAD_JURIDICA for o in oportunidades)

    def test_no_se_confunde_con_nuevo_director_juridico(self) -> None:
        """Un ascenso interno (CAMBIO_CARGO) NUNCA genera
        NUEVO_DIRECTOR_JURIDICO -- eso es solo para FUNCIONARIO_NUEVO."""
        d = _diferencia(
            TipoCambio.CAMBIO_CARGO, "Director Juridico",
            campos=(CampoModificadoDTO("cargo", "Asesor Juridico", "Director Juridico"),),
        )
        oportunidades = generar_oportunidades_funcionario(d, 1, 5, _AHORA)
        tipos = {o.tipo for o in oportunidades}
        assert TipoOportunidad.NUEVO_DIRECTOR_JURIDICO not in tipos

    def test_cambio_de_cargo_hacia_puesto_no_relevante_no_genera_nada(self) -> None:
        d = _diferencia(
            TipoCambio.CAMBIO_CARGO, "Chofer", campos=(CampoModificadoDTO("cargo", "Asistente", "Chofer"),)
        )
        assert generar_oportunidades_funcionario(d, 1, 5, _AHORA) == []


class TestCambioMasivoFuncionarios:
    def test_supera_umbral_absoluto_genera_oportunidad(self) -> None:
        stats = EstadisticasComparacionDTO(
            total_funcionarios_anteriores=100, total_funcionarios_actuales=100,
            cantidad_nuevos=20, cantidad_eliminados=0, cantidad_cambios=0, cantidad_sin_cambios=80,
            porcentaje_cambios=20.0,
        )
        oportunidades = generar_oportunidades_documento(stats, _REGLAS, entidad_id=1, detectado_en=_AHORA)
        assert any(o.tipo == TipoOportunidad.CAMBIO_MASIVO_FUNCIONARIOS for o in oportunidades)

    def test_bajo_ambos_umbrales_no_genera_oportunidad(self) -> None:
        stats = EstadisticasComparacionDTO(
            total_funcionarios_anteriores=50, total_funcionarios_actuales=50,
            cantidad_nuevos=1, cantidad_eliminados=0, cantidad_cambios=0, cantidad_sin_cambios=49,
            porcentaje_cambios=2.0,
        )
        assert generar_oportunidades_documento(stats, _REGLAS, 1, _AHORA) == []
