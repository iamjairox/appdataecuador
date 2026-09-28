"""Tests: RegistroForoService (Submodulos 8.6/8.14, versionado)."""

from __future__ import annotations

from datetime import UTC, date, datetime

from govdata.application.dto.diferencia_registro_foro_dto import (
    CampoModificadoForoDTO,
    DiferenciaRegistroForoDTO,
)
from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.services.registro_foro_service import RegistroForoService
from govdata.domain.value_objects.estado_registro_foro import EstadoRegistroForo
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo
from tests.unit.application.fakes_modulo8 import (
    FakeHistorialForoRepository,
    FakeRegistroForoRepository,
    FakeRegistroForoVersionRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_FECHA = date(2026, 1, 1)


def _registro_foro(**kwargs) -> RegistroForoDTO:
    base = {"nombre_completo": "Juan Perez", "provincia": "Pichincha", "estado": "VIGENTE", "registro": "R1"}
    base.update(kwargs)
    return RegistroForoDTO(**base)


def _servicio():
    registro_repo = FakeRegistroForoRepository()
    version_repo = FakeRegistroForoVersionRepository()
    historial_repo = FakeHistorialForoRepository()
    return RegistroForoService(registro_repo, version_repo, historial_repo), registro_repo, version_repo, historial_repo


class TestAplicarDiferencia:
    def test_sin_cambios_no_hace_nada(self) -> None:
        servicio, registro_repo, version_repo, historial_repo = _servicio()
        diferencia = DiferenciaRegistroForoDTO(tipo_cambio=TipoCambioForo.SIN_CAMBIOS, clave_registro="x")
        resultado = servicio.aplicar_diferencia(diferencia, 1, 1, _FECHA, _AHORA)
        assert resultado is None
        assert registro_repo.guardados == []
        assert version_repo.guardadas == []
        assert historial_repo.guardados == []

    def test_dato_nuevo_crea_version_1_y_puntero_vigente(self) -> None:
        servicio, _registro_repo, version_repo, historial_repo = _servicio()
        diferencia = DiferenciaRegistroForoDTO(
            tipo_cambio=TipoCambioForo.DATO_NUEVO, clave_registro="clave-1", datos_actuales=_registro_foro()
        )
        resultado = servicio.aplicar_diferencia(diferencia, 1, 1, _FECHA, _AHORA)
        assert resultado is not None
        assert resultado.numero_version == 1
        assert resultado.vigente
        assert resultado.estado == EstadoRegistroForo.VIGENTE
        assert len(version_repo.guardadas) == 1
        assert len(historial_repo.guardados) == 1

    def test_cambio_cierra_version_anterior_y_abre_la_siguiente(self) -> None:
        servicio, _registro_repo, version_repo, _historial_repo = _servicio()
        diferencia_1 = DiferenciaRegistroForoDTO(
            tipo_cambio=TipoCambioForo.DATO_NUEVO, clave_registro="clave-1", datos_actuales=_registro_foro()
        )
        servicio.aplicar_diferencia(diferencia_1, 1, 1, _FECHA, _AHORA)

        diferencia_2 = DiferenciaRegistroForoDTO(
            tipo_cambio=TipoCambioForo.CAMBIO_ESTADO, clave_registro="clave-1",
            datos_actuales=_registro_foro(estado="SUSPENDIDO"),
            datos_anteriores=_registro_foro(estado="VIGENTE"),
            campos_modificados=(CampoModificadoForoDTO("estado", "VIGENTE", "SUSPENDIDO"),),
        )
        resultado = servicio.aplicar_diferencia(diferencia_2, 1, 2, date(2026, 2, 1), _AHORA)

        assert resultado is not None
        assert resultado.numero_version == 2
        assert resultado.estado == EstadoRegistroForo.SUSPENDIDO
        assert len(version_repo.guardadas) == 2
        version_1 = next(v for v in version_repo.guardadas if v.numero_version == 1)
        assert not version_1.vigente

    def test_dato_eliminado_cierra_puntero_y_version(self) -> None:
        servicio, _registro_repo, version_repo, historial_repo = _servicio()
        diferencia_1 = DiferenciaRegistroForoDTO(
            tipo_cambio=TipoCambioForo.DATO_NUEVO, clave_registro="clave-1", datos_actuales=_registro_foro()
        )
        servicio.aplicar_diferencia(diferencia_1, 1, 1, _FECHA, _AHORA)

        diferencia_2 = DiferenciaRegistroForoDTO(tipo_cambio=TipoCambioForo.DATO_ELIMINADO, clave_registro="clave-1")
        resultado = servicio.aplicar_diferencia(diferencia_2, 1, 2, date(2026, 2, 1), _AHORA)

        assert resultado is not None
        assert not resultado.vigente
        version_1 = version_repo.guardadas[0]
        assert not version_1.vigente
        assert len(historial_repo.guardados) == 2

    def test_dato_eliminado_sin_puntero_previo_no_falla(self) -> None:
        servicio, *_ = _servicio()
        diferencia = DiferenciaRegistroForoDTO(tipo_cambio=TipoCambioForo.DATO_ELIMINADO, clave_registro="fantasma")
        resultado = servicio.aplicar_diferencia(diferencia, 1, 1, _FECHA, _AHORA)
        assert resultado is None

    def test_cambio_de_clave_cierra_fila_vieja_y_crea_una_nueva_preservando_numero_version(self) -> None:
        servicio, registro_repo, _version_repo, _historial_repo = _servicio()
        diferencia_1 = DiferenciaRegistroForoDTO(
            tipo_cambio=TipoCambioForo.DATO_NUEVO, clave_registro="sin_registro:x",
            datos_actuales=_registro_foro(registro=None),
        )
        servicio.aplicar_diferencia(diferencia_1, 1, 1, _FECHA, _AHORA)

        diferencia_2 = DiferenciaRegistroForoDTO(
            tipo_cambio=TipoCambioForo.CAMBIO_REGISTRO, clave_registro="registro:reg 1",
            clave_registro_anterior="sin_registro:x",
            datos_actuales=_registro_foro(registro="REG-1"),
            datos_anteriores=_registro_foro(registro=None),
            campos_modificados=(CampoModificadoForoDTO("registro", None, "REG-1"),),
        )
        resultado = servicio.aplicar_diferencia(diferencia_2, 1, 2, date(2026, 2, 1), _AHORA)

        assert resultado is not None
        assert resultado.clave_registro == "registro:reg 1"
        assert resultado.numero_version == 2  # continuidad preservada

        fila_vieja = next(r for r in registro_repo.guardados if r.clave_registro == "sin_registro:x")
        assert not fila_vieja.vigente
        fila_nueva = next(r for r in registro_repo.guardados if r.clave_registro == "registro:reg 1")
        assert fila_nueva.vigente
