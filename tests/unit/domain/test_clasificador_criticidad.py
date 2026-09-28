"""Tests: Clasificador de Criticidad (Modulo 5, sugerencia del cliente)."""

from __future__ import annotations

from govdata.application.dto.diferencia_dto import CampoModificadoDTO, DiferenciaFuncionarioDTO
from govdata.domain.rules.clasificador_criticidad import (
    clasificar_criticidad,
    enriquecer_con_criticidad,
)
from govdata.domain.rules.reglas_configurables import ReglasCriticidad
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_cambio import TipoCambio

_REGLAS = ReglasCriticidad(
    umbral_score_minimo=80.0,
    cargos_criticos=["Director Juridico", "Procurador"],
    cargos_altos=["Abogado", "Coordinador Juridico"],
    campos_medios=["correo", "telefono"],
    umbral_cambio_masivo_pct=30.0,
    umbral_cambio_masivo_absoluto=15,
)


def _diferencia(tipo: TipoCambio, cargo: str = "Chofer", campos: tuple = ()) -> DiferenciaFuncionarioDTO:
    return DiferenciaFuncionarioDTO(
        tipo_cambio=tipo, fingerprint="X", nombre="N", apellido="A", cargo=cargo,
        dependencia="Dep", correo=None, telefono=None, area="juridica", campos_modificados=campos,
    )


class TestNivelCritico:
    def test_cargo_critico_por_funcionario_nuevo(self) -> None:
        d = _diferencia(TipoCambio.FUNCIONARIO_NUEVO, cargo="Director Juridico")
        assert clasificar_criticidad(d, _REGLAS) == NivelCriticidad.CRITICO

    def test_cargo_critico_por_funcionario_eliminado(self) -> None:
        d = _diferencia(TipoCambio.FUNCIONARIO_ELIMINADO, cargo="Procurador")
        assert clasificar_criticidad(d, _REGLAS) == NivelCriticidad.CRITICO

    def test_cargo_critico_gana_sobre_campo_medio(self) -> None:
        """Un cambio de correo de un Director Juridico sigue siendo
        CRITICO -- el cargo pesa mas que el campo modificado."""
        d = _diferencia(TipoCambio.CAMBIO_CORREO, cargo="Director Juridico", campos=(CampoModificadoDTO("correo", "a", "b"),))
        assert clasificar_criticidad(d, _REGLAS) == NivelCriticidad.CRITICO


class TestNivelAlto:
    def test_cargo_alto(self) -> None:
        d = _diferencia(TipoCambio.FUNCIONARIO_NUEVO, cargo="Abogado")
        assert clasificar_criticidad(d, _REGLAS) == NivelCriticidad.ALTO


class TestNivelMedio:
    def test_cambio_de_correo_cargo_no_especial(self) -> None:
        d = _diferencia(TipoCambio.CAMBIO_CORREO, cargo="Chofer", campos=(CampoModificadoDTO("correo", "a", "b"),))
        assert clasificar_criticidad(d, _REGLAS) == NivelCriticidad.MEDIO

    def test_cambio_de_telefono_cargo_no_especial(self) -> None:
        d = _diferencia(TipoCambio.CAMBIO_TELEFONO, cargo="Chofer", campos=(CampoModificadoDTO("telefono", "a", "b"),))
        assert clasificar_criticidad(d, _REGLAS) == NivelCriticidad.MEDIO

    def test_cambio_de_cargo_o_dependencia_sin_ser_especial_es_medio_por_defecto(self) -> None:
        d = _diferencia(TipoCambio.CAMBIO_DEPENDENCIA, cargo="Chofer", campos=(CampoModificadoDTO("dependencia", "a", "b"),))
        assert clasificar_criticidad(d, _REGLAS) == NivelCriticidad.MEDIO

    def test_cambio_multiple_con_campo_medio(self) -> None:
        d = _diferencia(
            TipoCambio.CAMBIO_MULTIPLE, cargo="Chofer",
            campos=(CampoModificadoDTO("correo", "a", "b"), CampoModificadoDTO("dependencia", "x", "y")),
        )
        assert clasificar_criticidad(d, _REGLAS) == NivelCriticidad.MEDIO


class TestNivelBajo:
    def test_cambio_de_nombre_es_bajo(self) -> None:
        d = _diferencia(TipoCambio.CAMBIO_NOMBRE, cargo="Chofer", campos=(CampoModificadoDTO("nombre", "Juan", "Juann"),))
        assert clasificar_criticidad(d, _REGLAS) == NivelCriticidad.BAJO

    def test_cambio_de_apellido_es_bajo(self) -> None:
        d = _diferencia(TipoCambio.CAMBIO_APELLIDO, cargo="Chofer", campos=(CampoModificadoDTO("apellido", "P", "Pz"),))
        assert clasificar_criticidad(d, _REGLAS) == NivelCriticidad.BAJO

    def test_sin_cambios_es_bajo(self) -> None:
        d = _diferencia(TipoCambio.SIN_CAMBIOS, cargo="Chofer")
        assert clasificar_criticidad(d, _REGLAS) == NivelCriticidad.BAJO

    def test_cambio_multiple_solo_nombre_y_apellido_es_bajo(self) -> None:
        d = _diferencia(
            TipoCambio.CAMBIO_MULTIPLE, cargo="Chofer",
            campos=(CampoModificadoDTO("nombre", "Juan", "Juann"), CampoModificadoDTO("apellido", "P", "Pz")),
        )
        assert clasificar_criticidad(d, _REGLAS) == NivelCriticidad.BAJO


class TestEnriquecerConCriticidad:
    def test_asigna_criticidad_a_cada_diferencia_preservando_el_resto(self) -> None:
        diferencias = [_diferencia(TipoCambio.FUNCIONARIO_NUEVO, cargo="Director Juridico")]
        enriquecidas = enriquecer_con_criticidad(diferencias, _REGLAS)
        assert enriquecidas[0].criticidad == NivelCriticidad.CRITICO
        assert enriquecidas[0].tipo_cambio == TipoCambio.FUNCIONARIO_NUEVO
        assert diferencias[0].criticidad is None  # el original no se muta
