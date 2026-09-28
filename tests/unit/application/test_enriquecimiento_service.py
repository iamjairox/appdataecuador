"""Tests: EnriquecimientoService (Submodulo 6.7, pipeline completo)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.application.services.alerta_perfil_service import AlertaPerfilService
from govdata.application.services.auditoria_consulta_fuente_service import (
    AuditoriaConsultaFuenteService,
)
from govdata.application.services.cache_fuente_service import CacheFuenteService
from govdata.application.services.enriquecimiento_service import EnriquecimientoService
from govdata.application.services.evento_perfil_service import EventoPerfilService
from govdata.application.services.registro_fuente_service import RegistroFuenteService
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import GovDataError
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
_REGLAS_CACHE = ReglasCachePorFuente(dias_por_fuente={}, dias_defecto=7)


def _pm(persona_master_repo: FakePersonaMasterRepository) -> PersonaMaster:
    return persona_master_repo.guardar(PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez")))


def _servicio():
    persona_master_repo = FakePersonaMasterRepository()
    log_repo = FakeConsultaFuenteLogRepository()
    registro_repo = FakeRegistroFuenteRepository()
    atributo_repo = FakeAtributoTrazableRepository()
    alerta_repo = FakeAlertaPerfilRepository()
    evento_repo = FakeEventoPerfilRepository()

    cache_service = CacheFuenteService(log_repo, _REGLAS_CACHE)
    registro_fuente_service = RegistroFuenteService(registro_repo, atributo_repo)
    auditoria_service = AuditoriaConsultaFuenteService(log_repo, ahora_provider=lambda: _AHORA)
    alerta_service = AlertaPerfilService(alerta_repo)
    evento_service = EventoPerfilService(evento_repo)

    servicio = EnriquecimientoService(
        cache_service, registro_fuente_service, auditoria_service, alerta_service, evento_service,
        persona_master_repo, ahora_provider=lambda: _AHORA,
    )
    return servicio, persona_master_repo, log_repo, registro_repo, alerta_repo, evento_repo


def _senales() -> SenalesIdentidadDTO:
    return SenalesIdentidadDTO(nombre="Juan", apellido="Perez")


class TestEnriquecer:
    def test_fuente_con_datos_genera_registro_evento_y_actualiza_persona_master(self) -> None:
        servicio, persona_master_repo, log_repo, registro_repo, _alerta_repo, _evento_repo = _servicio()
        pm = _pm(persona_master_repo)
        fuente = FakeExternalSourcePort(
            FuenteExterna.SENESCYT, datos_por_llamada=[{"titulo": "Abogado"}], ahora_provider=lambda: _AHORA
        )

        resultado = servicio.enriquecer(pm, [fuente], _senales())

        assert resultado.fuentes_consultadas == ["senescyt"]
        assert resultado.fuentes_con_error == []
        assert resultado.fuentes_omitidas_por_cache == []
        assert resultado.eventos_generados >= 2  # NUEVA_FUENTE + PERSONA_ENRIQUECIDA + NUEVO_TITULO
        assert pm.cantidad_fuentes == 2
        assert len(registro_repo.guardados) == 1
        assert len(log_repo.guardados) == 1
        assert log_repo.guardados[0].exito is True

    def test_fuente_sin_resultados_no_genera_eventos_ni_alertas(self) -> None:
        servicio, persona_master_repo, *_ = _servicio()
        pm = _pm(persona_master_repo)
        fuente = FakeExternalSourcePort(FuenteExterna.SRI, datos_por_llamada=[], ahora_provider=lambda: _AHORA)

        resultado = servicio.enriquecer(pm, [fuente], _senales())
        assert resultado.fuentes_consultadas == ["sri"]
        assert resultado.eventos_generados == 0
        assert resultado.alertas_generadas == 0

    def test_fuente_que_falla_no_bloquea_las_demas(self) -> None:
        servicio, persona_master_repo, log_repo, *_ = _servicio()
        pm = _pm(persona_master_repo)
        fuente_falla = FakeExternalSourcePort(
            FuenteExterna.SRI, error=GovDataError("timeout"), ahora_provider=lambda: _AHORA
        )
        fuente_ok = FakeExternalSourcePort(
            FuenteExterna.SENESCYT, datos_por_llamada=[{"titulo": "Abogado"}], ahora_provider=lambda: _AHORA
        )

        resultado = servicio.enriquecer(pm, [fuente_falla, fuente_ok], _senales())

        assert resultado.fuentes_con_error == ["sri"]
        assert resultado.fuentes_consultadas == ["senescyt"]
        log_sri = next(log for log in log_repo.guardados if log.fuente == FuenteExterna.SRI)
        assert log_sri.exito is False
        assert log_sri.error == "timeout"

    def test_segunda_consulta_dentro_de_vigencia_se_omite_por_cache(self) -> None:
        servicio, persona_master_repo, *_ = _servicio()
        pm = _pm(persona_master_repo)
        fuente = FakeExternalSourcePort(
            FuenteExterna.SENESCYT, datos_por_llamada=[{"titulo": "Abogado"}], ahora_provider=lambda: _AHORA
        )

        servicio.enriquecer(pm, [fuente], _senales())
        resultado_2 = servicio.enriquecer(pm, [fuente], _senales())

        assert resultado_2.fuentes_omitidas_por_cache == ["senescyt"]
        assert fuente.llamadas == 1  # nunca se volvio a invocar la fuente

    def test_cambio_real_entre_dos_consultas_genera_alerta(self) -> None:
        servicio, persona_master_repo, log_repo, *_ = _servicio()
        pm = _pm(persona_master_repo)
        fuente = FakeExternalSourcePort(
            FuenteExterna.SENESCYT,
            datos_por_llamada=[{"titulo": "Abogado"}, {"titulo": "Doctor en Jurisprudencia"}],
            ahora_provider=lambda: _AHORA,
        )

        servicio.enriquecer(pm, [fuente], _senales())
        # forzar que el cache permita la segunda consulta (vigencia agotada simulada
        # invalidando el ultimo log a fallido no es trivial con el fake; en su lugar,
        # se limpia el historial de logs para simular "vigencia vencida")
        log_repo.guardados.clear()

        resultado_2 = servicio.enriquecer(pm, [fuente], _senales())
        assert resultado_2.alertas_generadas == 1
