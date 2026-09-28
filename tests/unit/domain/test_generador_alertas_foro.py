"""Tests: generador de Alertas del Foro -- Submodulo 8.7."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.diferencia_registro_foro_dto import (
    CampoModificadoForoDTO,
    DiferenciaRegistroForoDTO,
)
from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.domain.rules.generador_alertas_foro import generar_alertas_por_diferencia
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_foro import TipoAlertaForo
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestGenerarAlertas:
    def test_dato_nuevo_genera_alerta_registro_nuevo(self) -> None:
        diferencia = DiferenciaRegistroForoDTO(
            tipo_cambio=TipoCambioForo.DATO_NUEVO, clave_registro="r1", datos_actuales=RegistroForoDTO(registro="R1")
        )
        alertas = generar_alertas_por_diferencia(diferencia, 1, _AHORA)
        assert len(alertas) == 1
        assert alertas[0].tipo == TipoAlertaForo.REGISTRO_NUEVO
        assert alertas[0].prioridad == NivelCriticidad.MEDIO

    def test_dato_eliminado_genera_alerta_critica_alta(self) -> None:
        diferencia = DiferenciaRegistroForoDTO(
            tipo_cambio=TipoCambioForo.DATO_ELIMINADO, clave_registro="r1",
            datos_anteriores=RegistroForoDTO(registro="R1"),
        )
        alertas = generar_alertas_por_diferencia(diferencia, 1, _AHORA)
        assert alertas[0].tipo == TipoAlertaForo.REGISTRO_ELIMINADO
        assert alertas[0].prioridad == NivelCriticidad.ALTO

    def test_cambio_estado_genera_alerta(self) -> None:
        diferencia = DiferenciaRegistroForoDTO(
            tipo_cambio=TipoCambioForo.CAMBIO_ESTADO, clave_registro="r1",
            campos_modificados=(CampoModificadoForoDTO("estado", "VIGENTE", "SUSPENDIDO"),),
        )
        alertas = generar_alertas_por_diferencia(diferencia, 1, _AHORA)
        assert alertas[0].tipo == TipoAlertaForo.CAMBIO_ESTADO

    def test_cambio_dato_genera_alerta_baja(self) -> None:
        diferencia = DiferenciaRegistroForoDTO(
            tipo_cambio=TipoCambioForo.CAMBIO_DATO, clave_registro="r1",
            campos_modificados=(CampoModificadoForoDTO("nombre_completo", "Juan", "Juan A."),),
        )
        alertas = generar_alertas_por_diferencia(diferencia, 1, _AHORA)
        assert alertas[0].tipo == TipoAlertaForo.CAMBIO_DATO
        assert alertas[0].prioridad == NivelCriticidad.BAJO

    def test_sin_cambios_no_genera_alertas(self) -> None:
        diferencia = DiferenciaRegistroForoDTO(tipo_cambio=TipoCambioForo.SIN_CAMBIOS, clave_registro="r1")
        assert generar_alertas_por_diferencia(diferencia, 1, _AHORA) == []
