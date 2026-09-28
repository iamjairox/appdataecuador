"""Tests: PersistenciaInteligenteService (Submodulo 5.11) -- insertar,
actualizar, ignorar, versionar segun el tipo de cambio."""

from __future__ import annotations

from datetime import date

from govdata.application.dto.diferencia_dto import CampoModificadoDTO, DiferenciaFuncionarioDTO
from govdata.application.services.historial_service import HistorialService
from govdata.application.services.persistencia_inteligente_service import (
    PersistenciaInteligenteService,
)
from govdata.domain.value_objects.cargo import Cargo
from govdata.domain.value_objects.tipo_cambio import TipoCambio
from tests.unit.application.fakes_extraccion import (
    FakeFuncionarioRepositoryExtraccion,
    FakePersonaRepository,
)
from tests.unit.application.fakes_modulo5 import FakeVersionFuncionarioRepository


def _servicio():
    persona_repo = FakePersonaRepository()
    funcionario_repo = FakeFuncionarioRepositoryExtraccion()
    version_repo = FakeVersionFuncionarioRepository()
    historial = HistorialService(version_repo)
    servicio = PersistenciaInteligenteService(persona_repo, funcionario_repo, historial)
    return servicio, persona_repo, funcionario_repo, version_repo


def _diferencia(
    tipo: TipoCambio, fingerprint="JUANPEREZ", nombre="Juan", apellido="Perez", cargo="Director Juridico",
    dependencia="Legal", campos: tuple = (),
) -> DiferenciaFuncionarioDTO:
    return DiferenciaFuncionarioDTO(
        tipo_cambio=tipo, fingerprint=fingerprint, nombre=nombre, apellido=apellido, cargo=cargo,
        dependencia=dependencia, correo="j@x.com", telefono="0999", area="juridica", campos_modificados=campos,
    )


class TestInsertar:
    def test_funcionario_nuevo_inserta_persona_funcionario_y_version(self) -> None:
        servicio, persona_repo, funcionario_repo, version_repo = _servicio()
        resumen = servicio.aplicar([_diferencia(TipoCambio.FUNCIONARIO_NUEVO)], entidad_id=1, documento_id=10, fecha=date(2026, 6, 1))

        assert resumen.insertados == 1
        assert resumen.actualizados == 0
        assert resumen.versionados == 1
        assert len(persona_repo.guardadas) == 1
        assert len(funcionario_repo.guardados) == 1
        assert len(version_repo.guardadas) == 1
        assert "JUANPEREZ" in resumen.persona_id_por_fingerprint


class TestIgnorar:
    def test_sin_cambios_no_persiste_nada(self) -> None:
        servicio, persona_repo, funcionario_repo, version_repo = _servicio()
        resumen = servicio.aplicar([_diferencia(TipoCambio.SIN_CAMBIOS)], 1, 10, date(2026, 6, 1))
        assert resumen.ignorados == 1
        assert persona_repo.guardadas == []
        assert funcionario_repo.guardados == []
        assert version_repo.guardadas == []


class TestActualizar:
    def test_cambio_de_cargo_actualiza_persona_y_funcionario_existentes(self) -> None:
        servicio, persona_repo, funcionario_repo, version_repo = _servicio()
        servicio.aplicar([_diferencia(TipoCambio.FUNCIONARIO_NUEVO, cargo="Asesor Juridico")], 1, 10, date(2026, 6, 1))

        cambio = _diferencia(TipoCambio.CAMBIO_CARGO, cargo="Director Juridico", campos=(CampoModificadoDTO("cargo", "Asesor Juridico", "Director Juridico"),))
        resumen = servicio.aplicar([cambio], 1, 11, date(2026, 7, 1))

        assert resumen.actualizados == 1
        assert resumen.insertados == 0
        assert len(persona_repo.guardadas) == 1  # no duplica la persona
        assert funcionario_repo.guardados[0].cargo == Cargo("Director Juridico")
        assert len(version_repo.guardadas) == 2  # v1 cerrada + v2 abierta


class TestVersionarEliminado:
    def test_eliminado_cierra_funcionario_y_version_sin_duplicar_persona(self) -> None:
        servicio, _persona_repo, funcionario_repo, version_repo = _servicio()
        servicio.aplicar([_diferencia(TipoCambio.FUNCIONARIO_NUEVO)], 1, 10, date(2026, 6, 1))

        resumen = servicio.aplicar([_diferencia(TipoCambio.FUNCIONARIO_ELIMINADO)], 1, 11, date(2026, 7, 1))
        assert resumen.versionados == 1
        assert funcionario_repo.guardados[0].fecha_fin == date(2026, 7, 1)
        assert version_repo.guardadas[0].vigente is False

    def test_eliminado_sin_persona_previa_no_falla(self) -> None:
        """Dato inconsistente (nunca se persistio esa persona) -- no debe
        tumbar el pipeline."""
        servicio, _persona_repo, funcionario_repo, _version_repo = _servicio()
        resumen = servicio.aplicar([_diferencia(TipoCambio.FUNCIONARIO_ELIMINADO, fingerprint="NOEXISTE")], 1, 10, date(2026, 6, 1))
        assert resumen.versionados == 1
        assert funcionario_repo.guardados == []


class TestReutilizaFuncionarioVigenteEnLugarDeDuplicar:
    def test_no_crea_un_segundo_funcionario_para_la_misma_persona_entidad(self) -> None:
        servicio, _persona_repo, funcionario_repo, _version_repo = _servicio()
        servicio.aplicar([_diferencia(TipoCambio.FUNCIONARIO_NUEVO, cargo="Asesor Juridico")], 1, 10, date(2026, 6, 1))
        cambio = _diferencia(
            TipoCambio.CAMBIO_DEPENDENCIA, dependencia="Procuraduria",
            campos=(CampoModificadoDTO("dependencia", "Legal", "Procuraduria"),),
        )
        servicio.aplicar([cambio], 1, 11, date(2026, 7, 1))
        assert len(funcionario_repo.guardados) == 1
