"""Tests: Generador de Alertas (Submodulo 5.6) -- todos los patrones
explicitos del cliente."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.diferencia_dto import CampoModificadoDTO, DiferenciaFuncionarioDTO
from govdata.application.dto.estadisticas_comparacion_dto import EstadisticasComparacionDTO
from govdata.domain.entities.alerta import TipoAlerta
from govdata.domain.rules.generador_alertas import (
    generar_alertas_documento,
    generar_alertas_funcionario,
)
from govdata.domain.rules.reglas_configurables import ReglasCriticidad
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_cambio import TipoCambio

_AHORA = datetime(2026, 7, 1, tzinfo=UTC)
_REGLAS = ReglasCriticidad(
    umbral_score_minimo=80.0,
    cargos_criticos=["Director Juridico", "Director Financiero", "Procurador"],
    cargos_altos=["Abogado"],
    campos_medios=["correo", "telefono"],
    umbral_cambio_masivo_pct=30.0,
    umbral_cambio_masivo_absoluto=15,
)


def _diferencia(tipo: TipoCambio, cargo: str, campos: tuple = (), criticidad=NivelCriticidad.MEDIO) -> DiferenciaFuncionarioDTO:
    return DiferenciaFuncionarioDTO(
        tipo_cambio=tipo, fingerprint="X", nombre="Juan", apellido="Perez", cargo=cargo,
        dependencia="Dep", correo=None, telefono=None, area="juridica",
        campos_modificados=campos, criticidad=criticidad,
    )


class TestAlertasPorCargoNuevo:
    def test_nuevo_director_juridico(self) -> None:
        d = _diferencia(TipoCambio.FUNCIONARIO_NUEVO, "Director Juridico", criticidad=NivelCriticidad.CRITICO)
        alertas = generar_alertas_funcionario(d, entidad_id=1, documento_id=10, persona_id=5, detectado_en=_AHORA)
        assert any(a.tipo == TipoAlerta.NUEVO_DIRECTOR_JURIDICO for a in alertas)
        assert alertas[0].persona_id == 5
        assert alertas[0].documento_id == 10

    def test_nuevo_director_financiero(self) -> None:
        d = _diferencia(TipoCambio.FUNCIONARIO_NUEVO, "Director Financiero")
        alertas = generar_alertas_funcionario(d, 1, 10, None, _AHORA)
        assert any(a.tipo == TipoAlerta.NUEVO_DIRECTOR_FINANCIERO for a in alertas)

    def test_nuevo_procurador(self) -> None:
        d = _diferencia(TipoCambio.FUNCIONARIO_NUEVO, "Procurador")
        alertas = generar_alertas_funcionario(d, 1, 10, None, _AHORA)
        assert any(a.tipo == TipoAlerta.NUEVO_PROCURADOR for a in alertas)

    def test_nuevo_abogado(self) -> None:
        d = _diferencia(TipoCambio.FUNCIONARIO_NUEVO, "Abogado")
        alertas = generar_alertas_funcionario(d, 1, 10, None, _AHORA)
        assert any(a.tipo == TipoAlerta.NUEVO_ABOGADO for a in alertas)

    def test_cargo_no_relevante_no_genera_alerta_de_cargo(self) -> None:
        d = _diferencia(TipoCambio.FUNCIONARIO_NUEVO, "Chofer")
        alertas = generar_alertas_funcionario(d, 1, 10, None, _AHORA)
        assert alertas == []


class TestAlertaFuncionarioEliminado:
    def test_eliminado_genera_alerta(self) -> None:
        d = _diferencia(TipoCambio.FUNCIONARIO_ELIMINADO, "Director Juridico", criticidad=NivelCriticidad.CRITICO)
        alertas = generar_alertas_funcionario(d, 1, 10, 5, _AHORA)
        assert any(a.tipo == TipoAlerta.FUNCIONARIO_ELIMINADO for a in alertas)


class TestAlertasPorCampoModificado:
    def test_cambio_correo(self) -> None:
        d = _diferencia(TipoCambio.CAMBIO_CORREO, "Chofer", campos=(CampoModificadoDTO("correo", "a", "b"),))
        alertas = generar_alertas_funcionario(d, 1, 10, None, _AHORA)
        assert any(a.tipo == TipoAlerta.CAMBIO_CORREO for a in alertas)

    def test_cambio_dependencia(self) -> None:
        d = _diferencia(TipoCambio.CAMBIO_DEPENDENCIA, "Chofer", campos=(CampoModificadoDTO("dependencia", "a", "b"),))
        alertas = generar_alertas_funcionario(d, 1, 10, None, _AHORA)
        assert any(a.tipo == TipoAlerta.CAMBIO_DEPENDENCIA for a in alertas)

    def test_cambio_cargo(self) -> None:
        d = _diferencia(TipoCambio.CAMBIO_CARGO, "Chofer", campos=(CampoModificadoDTO("cargo", "a", "b"),))
        alertas = generar_alertas_funcionario(d, 1, 10, None, _AHORA)
        assert any(a.tipo == TipoAlerta.CAMBIO_CARGO for a in alertas)

    def test_cambio_multiple_genera_una_alerta_por_campo_relevante(self) -> None:
        d = _diferencia(
            TipoCambio.CAMBIO_MULTIPLE, "Chofer",
            campos=(CampoModificadoDTO("correo", "a", "b"), CampoModificadoDTO("cargo", "x", "y")),
        )
        alertas = generar_alertas_funcionario(d, 1, 10, None, _AHORA)
        tipos = {a.tipo for a in alertas}
        assert TipoAlerta.CAMBIO_CORREO in tipos
        assert TipoAlerta.CAMBIO_CARGO in tipos

    def test_sin_cambios_no_genera_ninguna_alerta(self) -> None:
        d = _diferencia(TipoCambio.SIN_CAMBIOS, "Director Juridico")
        assert generar_alertas_funcionario(d, 1, 10, None, _AHORA) == []


class TestAlertasDeDocumento:
    def test_cambio_masivo_por_umbral_absoluto(self) -> None:
        stats = EstadisticasComparacionDTO(
            total_funcionarios_anteriores=100, total_funcionarios_actuales=100,
            cantidad_nuevos=10, cantidad_eliminados=5, cantidad_cambios=2, cantidad_sin_cambios=83,
            porcentaje_cambios=17.0,
        )
        alertas = generar_alertas_documento(stats, _REGLAS, entidad_id=1, documento_id=10, detectado_en=_AHORA)
        assert any(a.tipo == TipoAlerta.CAMBIO_MASIVO for a in alertas)
        assert not any(a.tipo == TipoAlerta.CAMBIO_SUPERIOR_30_PORCIENTO for a in alertas)

    def test_cambio_superior_30_porciento_por_umbral_relativo(self) -> None:
        stats = EstadisticasComparacionDTO(
            total_funcionarios_anteriores=10, total_funcionarios_actuales=10,
            cantidad_nuevos=2, cantidad_eliminados=1, cantidad_cambios=1, cantidad_sin_cambios=6,
            porcentaje_cambios=40.0,
        )
        alertas = generar_alertas_documento(stats, _REGLAS, entidad_id=1, documento_id=10, detectado_en=_AHORA)
        assert any(a.tipo == TipoAlerta.CAMBIO_SUPERIOR_30_PORCIENTO for a in alertas)

    def test_ambos_umbrales_pueden_dispararse_juntos(self) -> None:
        stats = EstadisticasComparacionDTO(
            total_funcionarios_anteriores=20, total_funcionarios_actuales=20,
            cantidad_nuevos=15, cantidad_eliminados=0, cantidad_cambios=0, cantidad_sin_cambios=5,
            porcentaje_cambios=75.0,
        )
        alertas = generar_alertas_documento(stats, _REGLAS, entidad_id=1, documento_id=10, detectado_en=_AHORA)
        tipos = {a.tipo for a in alertas}
        assert TipoAlerta.CAMBIO_MASIVO in tipos
        assert TipoAlerta.CAMBIO_SUPERIOR_30_PORCIENTO in tipos

    def test_documento_vacio(self) -> None:
        stats = EstadisticasComparacionDTO(
            total_funcionarios_anteriores=5, total_funcionarios_actuales=0,
            cantidad_nuevos=0, cantidad_eliminados=5, cantidad_cambios=0, cantidad_sin_cambios=0,
            porcentaje_cambios=100.0,
        )
        alertas = generar_alertas_documento(stats, _REGLAS, entidad_id=1, documento_id=10, detectado_en=_AHORA)
        assert any(a.tipo == TipoAlerta.DOCUMENTO_VACIO for a in alertas)

    def test_documento_sospechoso_caida_abrupta_sin_llegar_a_cero(self) -> None:
        stats = EstadisticasComparacionDTO(
            total_funcionarios_anteriores=100, total_funcionarios_actuales=3,
            cantidad_nuevos=0, cantidad_eliminados=97, cantidad_cambios=0, cantidad_sin_cambios=3,
            porcentaje_cambios=97.0,
        )
        alertas = generar_alertas_documento(stats, _REGLAS, entidad_id=1, documento_id=10, detectado_en=_AHORA)
        assert any(a.tipo == TipoAlerta.DOCUMENTO_SOSPECHOSO for a in alertas)

    def test_sin_condiciones_no_genera_alertas_de_documento(self) -> None:
        stats = EstadisticasComparacionDTO(
            total_funcionarios_anteriores=50, total_funcionarios_actuales=50,
            cantidad_nuevos=1, cantidad_eliminados=0, cantidad_cambios=0, cantidad_sin_cambios=49,
            porcentaje_cambios=2.0,
        )
        alertas = generar_alertas_documento(stats, _REGLAS, entidad_id=1, documento_id=10, detectado_en=_AHORA)
        assert alertas == []
