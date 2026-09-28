"""Tests: PerfilAcademicoService (Submodulo 7.16, contrato oficial)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from govdata.application.services.perfil_academico_service import PerfilAcademicoService
from govdata.domain.entities.alerta_academica import AlertaAcademica
from govdata.domain.entities.evento_academico import EventoAcademico
from govdata.domain.entities.historial_academico import HistorialAcademico
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.entities.titulo_academico import TituloAcademico
from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.tipo_alerta_academica import TipoAlertaAcademica
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico
from govdata.domain.value_objects.tipo_evento_academico import TipoEventoAcademico
from tests.unit.application.fakes_modulo6 import FakePersonaMasterRepository
from tests.unit.application.fakes_modulo7 import (
    FakeAlertaAcademicaRepository,
    FakeEventoAcademicoRepository,
    FakeHistorialAcademicoRepository,
    FakeTituloAcademicoRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _servicio():
    pm_repo = FakePersonaMasterRepository()
    titulo_repo = FakeTituloAcademicoRepository()
    historial_repo = FakeHistorialAcademicoRepository()
    evento_repo = FakeEventoAcademicoRepository()
    alerta_repo = FakeAlertaAcademicaRepository()
    servicio = PerfilAcademicoService(pm_repo, titulo_repo, historial_repo, evento_repo, alerta_repo)
    return servicio, pm_repo, titulo_repo, historial_repo, evento_repo, alerta_repo


class TestConstruirPerfil:
    def test_persona_master_inexistente_falla(self) -> None:
        servicio, *_ = _servicio()
        with pytest.raises(PersonaMasterInvalidaError):
            servicio.construir_perfil(999)

    def test_perfil_completo_respeta_contrato_oficial(self) -> None:
        servicio, pm_repo, titulo_repo, historial_repo, evento_repo, alerta_repo = _servicio()
        pm = pm_repo.guardar(PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez")))

        titulo_repo.guardar(
            TituloAcademico(
                persona_master_id=pm.id, clave_titulo="registro:r1", titulo="ABOGADO", nivel="TERCER NIVEL",
                institucion="UCE",
            )
        )
        historial_repo.guardar_lote(
            [
                HistorialAcademico(
                    persona_master_id=pm.id, clave_titulo="registro:r1", tipo_cambio=TipoCambioAcademico.TITULO_NUEVO,
                    detectado_en=_AHORA, consulta_senescyt_id=1,
                )
            ]
        )
        evento_repo.guardar(
            EventoAcademico(tipo=TipoEventoAcademico.TITULO_NUEVO, persona_master_id=pm.id, payload={}, creado_en=_AHORA)
        )
        alerta_repo.guardar(
            AlertaAcademica(
                persona_master_id=pm.id, tipo=TipoAlertaAcademica.NUEVO_TITULO, prioridad=NivelCriticidad.MEDIO,
                descripcion="x", detectado_en=_AHORA,
            )
        )

        perfil = servicio.construir_perfil(pm.id)
        contrato = perfil.to_dict()

        assert set(contrato.keys()) == {
            "persona_master", "identidad", "titulos", "historial", "alertas", "eventos", "estadisticas", "generado_en",
        }
        assert contrato["persona_master"]["persona_master_id"] == pm.id
        assert len(contrato["titulos"]) == 1
        assert len(contrato["historial"]) == 1
        assert len(contrato["eventos"]) == 1
        assert len(contrato["alertas"]) == 1
        assert contrato["estadisticas"]["cantidad_titulos_vigentes"] == 1
