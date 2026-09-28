"""Tests: EnriquecerPersonaUseCase (Submodulo 6.7)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.services.alerta_perfil_service import AlertaPerfilService
from govdata.application.services.auditoria_consulta_fuente_service import (
    AuditoriaConsultaFuenteService,
)
from govdata.application.services.cache_fuente_service import CacheFuenteService
from govdata.application.services.enriquecimiento_service import EnriquecimientoService
from govdata.application.services.evento_perfil_service import EventoPerfilService
from govdata.application.services.registro_fuente_service import RegistroFuenteService
from govdata.application.use_cases.enriquecer_persona_use_case import EnriquecerPersonaUseCase
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.rules.reglas_identidad import ReglasCachePorFuente
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes_modulo6 import (
    FakeAlertaPerfilRepository,
    FakeAtributoTrazableRepository,
    FakeConsultaFuenteLogRepository,
    FakeEventoPerfilRepository,
    FakeExternalSourcePort,
    FakePersonaMasterRepository,
    FakeRegistroFuenteRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _caso_uso() -> tuple[EnriquecerPersonaUseCase, FakePersonaMasterRepository]:
    pm_repo = FakePersonaMasterRepository()
    log_repo = FakeConsultaFuenteLogRepository()
    registro_repo = FakeRegistroFuenteRepository()
    atributo_repo = FakeAtributoTrazableRepository()
    alerta_repo = FakeAlertaPerfilRepository()
    evento_repo = FakeEventoPerfilRepository()

    servicio = EnriquecimientoService(
        CacheFuenteService(log_repo, ReglasCachePorFuente()),
        RegistroFuenteService(registro_repo, atributo_repo),
        AuditoriaConsultaFuenteService(log_repo, ahora_provider=lambda: _AHORA),
        AlertaPerfilService(alerta_repo),
        EventoPerfilService(evento_repo),
        pm_repo,
        ahora_provider=lambda: _AHORA,
    )
    return EnriquecerPersonaUseCase(servicio), pm_repo


class TestEjecutar:
    def test_construye_senales_desde_persona_master_y_delega_al_servicio(self) -> None:
        caso_uso, pm_repo = _caso_uso()
        pm = pm_repo.guardar(PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez")))
        fuente = FakeExternalSourcePort(
            FuenteExterna.SENESCYT, datos_por_llamada=[{"titulo": "Abogado"}], ahora_provider=lambda: _AHORA
        )

        resultado = caso_uso.ejecutar(pm, [fuente], cargo="Director Juridico", institucion="DPE")
        assert resultado.persona_master_id == pm.id
        assert resultado.fuentes_consultadas == ["senescyt"]
