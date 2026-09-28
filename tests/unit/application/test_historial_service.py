"""Tests: HistorialService (Submodulos 5.2/5.3/5.4)."""

from __future__ import annotations

from datetime import date

from govdata.application.dto.diferencia_dto import CampoModificadoDTO, DiferenciaFuncionarioDTO
from govdata.application.services.historial_service import HistorialService
from govdata.domain.value_objects.tipo_cambio import TipoCambio
from tests.unit.application.fakes_modulo5 import FakeVersionFuncionarioRepository


def _diferencia(tipo: TipoCambio, cargo: str = "Director Juridico", dependencia: str = "Legal", campos: tuple = ()) -> DiferenciaFuncionarioDTO:
    return DiferenciaFuncionarioDTO(
        tipo_cambio=tipo, fingerprint="X", nombre="Juan", apellido="Perez", cargo=cargo,
        dependencia=dependencia, correo=None, telefono=None, area="juridica", campos_modificados=campos,
    )


class TestAplicarDiferencia:
    def test_nuevo_abre_version_1(self) -> None:
        repo = FakeVersionFuncionarioRepository()
        servicio = HistorialService(repo)
        d = _diferencia(TipoCambio.FUNCIONARIO_NUEVO)
        version = servicio.aplicar_diferencia(d, entidad_id=1, persona_id=5, funcionario_id=10, documento_id=100, fecha=date(2026, 6, 1))
        assert version.numero_version == 1
        assert version.vigente is True

    def test_cambio_cierra_vigente_y_abre_siguiente(self) -> None:
        repo = FakeVersionFuncionarioRepository()
        servicio = HistorialService(repo)
        d1 = _diferencia(TipoCambio.FUNCIONARIO_NUEVO, cargo="Asesor Juridico")
        servicio.aplicar_diferencia(d1, 1, 5, 10, 100, date(2026, 6, 1))

        d2 = _diferencia(TipoCambio.CAMBIO_CARGO, cargo="Director Juridico", campos=(CampoModificadoDTO("cargo", "Asesor Juridico", "Director Juridico"),))
        v2 = servicio.aplicar_diferencia(d2, 1, 5, 10, 101, date(2026, 7, 1))

        assert v2.numero_version == 2
        assert v2.vigente is True
        anteriores = [v for v in repo.guardadas if v.numero_version == 1]
        assert anteriores[0].vigente is False
        assert anteriores[0].fecha_fin == date(2026, 7, 1)

    def test_eliminado_cierra_vigente_sin_abrir_nueva(self) -> None:
        repo = FakeVersionFuncionarioRepository()
        servicio = HistorialService(repo)
        servicio.aplicar_diferencia(_diferencia(TipoCambio.FUNCIONARIO_NUEVO), 1, 5, 10, 100, date(2026, 6, 1))

        resultado = servicio.aplicar_diferencia(_diferencia(TipoCambio.FUNCIONARIO_ELIMINADO), 1, 5, 10, 101, date(2026, 7, 1))
        assert resultado.vigente is False
        assert len(repo.guardadas) == 1

    def test_sin_cambios_no_hace_nada(self) -> None:
        repo = FakeVersionFuncionarioRepository()
        servicio = HistorialService(repo)
        resultado = servicio.aplicar_diferencia(_diferencia(TipoCambio.SIN_CAMBIOS), 1, 5, 10, 100, date(2026, 6, 1))
        assert resultado is None
        assert repo.guardadas == []

    def test_eliminado_sin_version_previa_no_hace_nada(self) -> None:
        repo = FakeVersionFuncionarioRepository()
        servicio = HistorialService(repo)
        resultado = servicio.aplicar_diferencia(_diferencia(TipoCambio.FUNCIONARIO_ELIMINADO), 1, 5, 10, 100, date(2026, 6, 1))
        assert resultado is None


class TestConsultasDeCargo:
    def _preparar(self, repo: FakeVersionFuncionarioRepository) -> None:
        servicio = HistorialService(repo)
        # Persona 5: Director Juridico jun-jul, luego reemplazada.
        servicio.aplicar_diferencia(_diferencia(TipoCambio.FUNCIONARIO_NUEVO, cargo="Director Juridico"), 1, 5, 10, 100, date(2026, 6, 1))
        servicio.aplicar_diferencia(_diferencia(TipoCambio.FUNCIONARIO_ELIMINADO, cargo="Director Juridico"), 1, 5, 10, 101, date(2026, 7, 1))
        # Persona 6: Director Juridico desde julio.
        servicio.aplicar_diferencia(_diferencia(TipoCambio.FUNCIONARIO_NUEVO, cargo="Director Juridico"), 1, 6, 11, 101, date(2026, 7, 1))

    def test_quien_ocupa_cargo_ahora(self) -> None:
        repo = FakeVersionFuncionarioRepository()
        self._preparar(repo)
        servicio = HistorialService(repo)
        vigente = servicio.quien_ocupa_cargo_ahora(1, "Director Juridico")
        assert vigente is not None
        assert vigente.persona_id == 6

    def test_quien_ocupaba_cargo_en_fecha(self) -> None:
        repo = FakeVersionFuncionarioRepository()
        self._preparar(repo)
        servicio = HistorialService(repo)
        version = servicio.quien_ocupaba_cargo_en_fecha(1, "Director Juridico", date(2026, 6, 15))
        assert version is not None
        assert version.persona_id == 5

    def test_cantidad_de_personas_en_cargo(self) -> None:
        repo = FakeVersionFuncionarioRepository()
        self._preparar(repo)
        servicio = HistorialService(repo)
        assert servicio.cantidad_de_personas_en_cargo(1, "Director Juridico") == 2

    def test_historial_del_cargo_ordenado_cronologicamente(self) -> None:
        repo = FakeVersionFuncionarioRepository()
        self._preparar(repo)
        servicio = HistorialService(repo)
        historial = servicio.historial_del_cargo(1, "Director Juridico")
        assert [v.persona_id for v in historial] == [5, 6]

    def test_historial_de_persona(self) -> None:
        repo = FakeVersionFuncionarioRepository()
        self._preparar(repo)
        servicio = HistorialService(repo)
        historial = servicio.historial_de_persona(5)
        assert len(historial) == 1

    def test_historial_de_dependencias_agrupa_por_persona(self) -> None:
        repo = FakeVersionFuncionarioRepository()
        self._preparar(repo)
        servicio = HistorialService(repo)
        agrupado = servicio.historial_de_dependencias(1)
        assert set(agrupado.keys()) == {5, 6}


class TestCerrarVersionVigente:
    def test_sin_version_vigente_devuelve_none(self) -> None:
        repo = FakeVersionFuncionarioRepository()
        servicio = HistorialService(repo)
        assert servicio.cerrar_version_vigente(999, 1, date(2026, 6, 1)) is None
