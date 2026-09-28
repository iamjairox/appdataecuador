"""Tests: PerfilPersonaService (Submodulos 6.4 + 6.16, contrato oficial)."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from govdata.application.services.historial_service import HistorialService
from govdata.application.services.perfil_persona_service import PerfilPersonaService
from govdata.application.services.timeline_persona_service import TimelinePersonaService
from govdata.domain.entities.alerta_perfil import AlertaPerfil
from govdata.domain.entities.evento_perfil import EventoPerfil
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.entities.registro_fuente import RegistroFuente
from govdata.domain.entities.version_funcionario import VersionFuncionario
from govdata.domain.exceptions.domain_exceptions import PersonaMasterInvalidaError
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.tipo_alerta_perfil import TipoAlertaPerfil
from govdata.domain.value_objects.tipo_evento_identidad import TipoEventoIdentidad
from tests.unit.application.fakes_modulo5 import FakeVersionFuncionarioRepository
from tests.unit.application.fakes_modulo6 import (
    FakeAlertaPerfilRepository,
    FakeEventoPerfilRepository,
    FakePersonaMasterRepository,
    FakeRegistroFuenteRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _servicio():
    persona_master_repo = FakePersonaMasterRepository()
    registro_fuente_repo = FakeRegistroFuenteRepository()
    version_repo = FakeVersionFuncionarioRepository()
    historial_service = HistorialService(version_repo)
    evento_repo = FakeEventoPerfilRepository()
    alerta_repo = FakeAlertaPerfilRepository()
    timeline_service = TimelinePersonaService(historial_service, registro_fuente_repo)
    servicio = PerfilPersonaService(
        persona_master_repo, registro_fuente_repo, historial_service, evento_repo, alerta_repo, timeline_service
    )
    return servicio, persona_master_repo, registro_fuente_repo, version_repo, evento_repo, alerta_repo


class TestConstruirPerfil:
    def test_persona_master_inexistente_falla(self) -> None:
        servicio, *_ = _servicio()
        with pytest.raises(PersonaMasterInvalidaError):
            servicio.construir_perfil(999)

    def test_perfil_completo_respeta_el_contrato_oficial(self) -> None:
        servicio, pm_repo, registro_repo, version_repo, evento_repo, alerta_repo = _servicio()

        pm = pm_repo.guardar(PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez")))
        version_repo.guardar(
            VersionFuncionario(
                persona_id=1, entidad_id=1, numero_version=1, cargo="Director Juridico", dependencia="Legal",
                area="juridica", documento_id=1, fecha_inicio=date(2023, 1, 1),
            )
        )
        registro_repo.guardar(
            RegistroFuente(
                persona_master_id=pm.id, fuente=FuenteExterna.SENESCYT, version=1,
                datos={"titulo": "Abogado", "profesion": "Derecho"}, consultado_en=_AHORA,
            )
        )
        evento_repo.guardar(
            EventoPerfil(tipo=TipoEventoIdentidad.NUEVA_FUENTE, persona_master_id=pm.id, payload={}, creado_en=_AHORA)
        )
        alerta_repo.guardar(
            AlertaPerfil(
                persona_master_id=pm.id, tipo=TipoAlertaPerfil.TITULO_CAMBIADO,
                prioridad=NivelCriticidad.MEDIO, descripcion="x", detectado_en=_AHORA,
            )
        )

        perfil = servicio.construir_perfil(pm.id)

        # Contrato oficial 6.16: exactamente estas 9 claves de alto nivel.
        contrato = perfil.to_dict()
        assert set(contrato.keys()) == {
            "persona", "identidad", "perfil", "fuentes", "historial", "eventos", "alertas", "timeline",
            "estadisticas", "generado_en",
        }
        assert contrato["persona"]["nombre_completo"] == "JUAN PEREZ"
        assert contrato["identidad"]["persona_master_id"] == pm.id
        assert contrato["perfil"]["cargo_actual"] == "Director Juridico"
        assert "Abogado" in contrato["perfil"]["titulos"]
        assert "senescyt" in contrato["perfil"]["fuentes_consultadas"]
        assert len(contrato["fuentes"]) == 1
        assert len(contrato["historial"]) == 1
        assert len(contrato["eventos"]) == 1
        assert len(contrato["alertas"]) == 1
        assert contrato["estadisticas"]["cantidad_alertas"] == 1
        assert contrato["estadisticas"]["cantidad_eventos"] == 1
