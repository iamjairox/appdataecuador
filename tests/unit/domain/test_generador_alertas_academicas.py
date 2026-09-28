"""Tests: generador de Alertas Academicas (Submodulo 7.8)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.diferencia_titulo_dto import (
    CampoModificadoTituloDTO,
    DiferenciaTituloDTO,
)
from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.domain.rules.generador_alertas_academicas import generar_alertas_por_diferencia
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_academica import TipoAlertaAcademica
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _persona_academica(**kwargs) -> PersonaAcademicaDTO:
    base = {"titulo": "ABOGADO", "nivel": "TERCER NIVEL", "institucion": "UCE"}
    base.update(kwargs)
    return PersonaAcademicaDTO(**base)


class TestNuevoYEliminado:
    def test_nuevo_titulo(self) -> None:
        diferencia = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.TITULO_NUEVO, clave_titulo="x", datos_actuales=_persona_academica()
        )
        alertas = generar_alertas_por_diferencia(diferencia, 1, _AHORA)
        assert len(alertas) == 1
        assert alertas[0].tipo == TipoAlertaAcademica.NUEVO_TITULO

    def test_titulo_eliminado(self) -> None:
        diferencia = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.TITULO_ELIMINADO, clave_titulo="x", datos_anteriores=_persona_academica()
        )
        alertas = generar_alertas_por_diferencia(diferencia, 1, _AHORA)
        assert len(alertas) == 1
        assert alertas[0].tipo == TipoAlertaAcademica.TITULO_ELIMINADO
        assert alertas[0].prioridad == NivelCriticidad.ALTO


class TestCambiosDeCampo:
    def test_cambio_de_nivel(self) -> None:
        diferencia = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.CAMBIO_NIVEL, clave_titulo="x",
            campos_modificados=(CampoModificadoTituloDTO("nivel", "TERCER NIVEL", "CUARTO NIVEL"),),
        )
        alertas = generar_alertas_por_diferencia(diferencia, 1, _AHORA)
        assert len(alertas) == 1
        assert alertas[0].tipo == TipoAlertaAcademica.CAMBIO_NIVEL

    def test_cambio_de_institucion(self) -> None:
        diferencia = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.CAMBIO_UNIVERSIDAD, clave_titulo="x",
            campos_modificados=(CampoModificadoTituloDTO("institucion", "UCE", "PUCE"),),
        )
        alertas = generar_alertas_por_diferencia(diferencia, 1, _AHORA)
        assert alertas[0].tipo == TipoAlertaAcademica.CAMBIO_INSTITUCION

    def test_cambio_de_estado_generico(self) -> None:
        diferencia = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.CAMBIO_ESTADO, clave_titulo="x",
            campos_modificados=(CampoModificadoTituloDTO("estado", "VIGENTE", "EN_REVISION"),),
        )
        alertas = generar_alertas_por_diferencia(diferencia, 1, _AHORA)
        assert len(alertas) == 1
        assert alertas[0].tipo == TipoAlertaAcademica.CAMBIO_ESTADO

    def test_cambio_a_suspendido_genera_dos_alertas(self) -> None:
        diferencia = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.CAMBIO_ESTADO, clave_titulo="x",
            campos_modificados=(CampoModificadoTituloDTO("estado", "VIGENTE", "SUSPENDIDO"),),
        )
        alertas = generar_alertas_por_diferencia(diferencia, 1, _AHORA)
        tipos = {a.tipo for a in alertas}
        assert tipos == {TipoAlertaAcademica.CAMBIO_ESTADO, TipoAlertaAcademica.REGISTRO_SUSPENDIDO}
        suspendido = next(a for a in alertas if a.tipo == TipoAlertaAcademica.REGISTRO_SUSPENDIDO)
        assert suspendido.prioridad == NivelCriticidad.CRITICO

    def test_cambio_a_anulado_genera_dos_alertas(self) -> None:
        diferencia = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.CAMBIO_ESTADO, clave_titulo="x",
            campos_modificados=(CampoModificadoTituloDTO("estado", "VIGENTE", "ANULADO"),),
        )
        alertas = generar_alertas_por_diferencia(diferencia, 1, _AHORA)
        tipos = {a.tipo for a in alertas}
        assert tipos == {TipoAlertaAcademica.CAMBIO_ESTADO, TipoAlertaAcademica.REGISTRO_ANULADO}

    def test_cambio_multiple_genera_alerta_por_cada_campo_relevante(self) -> None:
        diferencia = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.CAMBIO_MULTIPLE, clave_titulo="x",
            campos_modificados=(
                CampoModificadoTituloDTO("nivel", "TERCER NIVEL", "CUARTO NIVEL"),
                CampoModificadoTituloDTO("institucion", "UCE", "PUCE"),
            ),
        )
        alertas = generar_alertas_por_diferencia(diferencia, 1, _AHORA)
        tipos = {a.tipo for a in alertas}
        assert tipos == {TipoAlertaAcademica.CAMBIO_NIVEL, TipoAlertaAcademica.CAMBIO_INSTITUCION}

    def test_sin_campos_relevantes_no_genera_alertas(self) -> None:
        diferencia = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.CAMBIO_MULTIPLE, clave_titulo="x",
            campos_modificados=(CampoModificadoTituloDTO("observaciones", "a", "b"),),
        )
        assert generar_alertas_por_diferencia(diferencia, 1, _AHORA) == []
