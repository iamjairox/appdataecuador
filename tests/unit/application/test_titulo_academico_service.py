"""Tests: TituloAcademicoService (Submodulos 7.6/7.14, versionado)."""

from __future__ import annotations

from datetime import UTC, date, datetime

from govdata.application.dto.diferencia_titulo_dto import (
    CampoModificadoTituloDTO,
    DiferenciaTituloDTO,
)
from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.application.services.titulo_academico_service import TituloAcademicoService
from govdata.domain.value_objects.estado_registro_academico import EstadoRegistroAcademico
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico
from tests.unit.application.fakes_modulo7 import (
    FakeHistorialAcademicoRepository,
    FakeTituloAcademicoRepository,
    FakeTituloVersionRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_FECHA = date(2026, 1, 1)


def _persona_academica(**kwargs) -> PersonaAcademicaDTO:
    base = {"titulo": "ABOGADO", "nivel": "TERCER NIVEL", "institucion": "UCE", "estado": "VIGENTE"}
    base.update(kwargs)
    return PersonaAcademicaDTO(**base)


def _servicio() -> tuple[TituloAcademicoService, FakeTituloAcademicoRepository, FakeTituloVersionRepository, FakeHistorialAcademicoRepository]:
    titulo_repo = FakeTituloAcademicoRepository()
    version_repo = FakeTituloVersionRepository()
    historial_repo = FakeHistorialAcademicoRepository()
    return TituloAcademicoService(titulo_repo, version_repo, historial_repo), titulo_repo, version_repo, historial_repo


class TestAplicarDiferencia:
    def test_sin_cambios_no_hace_nada(self) -> None:
        servicio, titulo_repo, version_repo, historial_repo = _servicio()
        diferencia = DiferenciaTituloDTO(tipo_cambio=TipoCambioAcademico.SIN_CAMBIOS, clave_titulo="x")
        resultado = servicio.aplicar_diferencia(diferencia, 1, 1, _FECHA, _AHORA)
        assert resultado is None
        assert titulo_repo.guardados == []
        assert version_repo.guardadas == []
        assert historial_repo.guardados == []

    def test_titulo_nuevo_crea_version_1_y_puntero_vigente(self) -> None:
        servicio, _titulo_repo, version_repo, historial_repo = _servicio()
        diferencia = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.TITULO_NUEVO, clave_titulo="clave-1", datos_actuales=_persona_academica()
        )
        resultado = servicio.aplicar_diferencia(diferencia, 1, 1, _FECHA, _AHORA)
        assert resultado is not None
        assert resultado.numero_version == 1
        assert resultado.vigente
        assert resultado.estado == EstadoRegistroAcademico.VIGENTE
        assert len(version_repo.guardadas) == 1
        assert version_repo.guardadas[0].numero_version == 1
        assert len(historial_repo.guardados) == 1

    def test_cambio_cierra_version_anterior_y_abre_la_siguiente(self) -> None:
        servicio, _titulo_repo, version_repo, _historial_repo = _servicio()
        diferencia_1 = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.TITULO_NUEVO, clave_titulo="clave-1", datos_actuales=_persona_academica()
        )
        servicio.aplicar_diferencia(diferencia_1, 1, 1, _FECHA, _AHORA)

        diferencia_2 = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.CAMBIO_ESTADO, clave_titulo="clave-1",
            datos_actuales=_persona_academica(estado="SUSPENDIDO"),
            datos_anteriores=_persona_academica(estado="VIGENTE"),
            campos_modificados=(CampoModificadoTituloDTO("estado", "VIGENTE", "SUSPENDIDO"),),
        )
        resultado = servicio.aplicar_diferencia(diferencia_2, 1, 2, date(2026, 2, 1), _AHORA)

        assert resultado is not None
        assert resultado.numero_version == 2
        assert resultado.estado == EstadoRegistroAcademico.SUSPENDIDO
        assert len(version_repo.guardadas) == 2
        version_1 = next(v for v in version_repo.guardadas if v.numero_version == 1)
        assert not version_1.vigente

    def test_titulo_eliminado_cierra_puntero_y_version(self) -> None:
        servicio, _titulo_repo, version_repo, historial_repo = _servicio()
        diferencia_1 = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.TITULO_NUEVO, clave_titulo="clave-1", datos_actuales=_persona_academica()
        )
        servicio.aplicar_diferencia(diferencia_1, 1, 1, _FECHA, _AHORA)

        diferencia_2 = DiferenciaTituloDTO(tipo_cambio=TipoCambioAcademico.TITULO_ELIMINADO, clave_titulo="clave-1")
        resultado = servicio.aplicar_diferencia(diferencia_2, 1, 2, date(2026, 2, 1), _AHORA)

        assert resultado is not None
        assert not resultado.vigente
        version_1 = version_repo.guardadas[0]
        assert not version_1.vigente
        assert len(historial_repo.guardados) == 2

    def test_titulo_eliminado_sin_puntero_previo_no_falla(self) -> None:
        servicio, *_ = _servicio()
        diferencia = DiferenciaTituloDTO(tipo_cambio=TipoCambioAcademico.TITULO_ELIMINADO, clave_titulo="fantasma")
        resultado = servicio.aplicar_diferencia(diferencia, 1, 1, _FECHA, _AHORA)
        assert resultado is None

    def test_cambio_de_clave_cierra_fila_vieja_y_crea_una_nueva_preservando_numero_version(self) -> None:
        """Cuando broto el numero_registro (Submodulo 7.7, emparejamiento
        de respaldo), la fila con la clave VIEJA se cierra y se crea una
        NUEVA bajo la clave nueva -- pero el numero_version continua
        (nunca se pierde la continuidad del historial)."""
        servicio, titulo_repo, _version_repo, _historial_repo = _servicio()
        diferencia_1 = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.TITULO_NUEVO, clave_titulo="sin_registro:x",
            datos_actuales=_persona_academica(numero_registro=None),
        )
        servicio.aplicar_diferencia(diferencia_1, 1, 1, _FECHA, _AHORA)

        diferencia_2 = DiferenciaTituloDTO(
            tipo_cambio=TipoCambioAcademico.CAMBIO_REGISTRO, clave_titulo="registro:reg 1",
            clave_titulo_anterior="sin_registro:x",
            datos_actuales=_persona_academica(numero_registro="REG-1"),
            datos_anteriores=_persona_academica(numero_registro=None),
            campos_modificados=(CampoModificadoTituloDTO("numero_registro", None, "REG-1"),),
        )
        resultado = servicio.aplicar_diferencia(diferencia_2, 1, 2, date(2026, 2, 1), _AHORA)

        assert resultado is not None
        assert resultado.clave_titulo == "registro:reg 1"
        assert resultado.numero_version == 2  # continuidad preservada

        fila_vieja = next(t for t in titulo_repo.guardados if t.clave_titulo == "sin_registro:x")
        assert not fila_vieja.vigente
        fila_nueva = next(t for t in titulo_repo.guardados if t.clave_titulo == "registro:reg 1")
        assert fila_nueva.vigente
