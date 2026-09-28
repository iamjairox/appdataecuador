"""Tests: EnriquecimientoForoService -- EL PIPELINE del Modulo 8 (tramo Foro)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.services.alerta_foro_service import AlertaForoService
from govdata.application.services.cache_foro_service import CacheForoService
from govdata.application.services.comparacion_foro_service import ComparacionForoService
from govdata.application.services.consulta_foro_service import ConsultaForoService
from govdata.application.services.enriquecimiento_foro_service import EnriquecimientoForoService
from govdata.application.services.evento_foro_service import EventoForoService
from govdata.application.services.registro_foro_service import RegistroForoService
from govdata.config.rule_engine_foro import cargar_rule_engine_foro
from govdata.domain.entities.persona import Persona
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import ConsultaForoFallidaError
from govdata.domain.rules.reglas_foro import ReglasCacheForo, RuleEngineForo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes_modulo8 import (
    FakeAlertaForoRepository,
    FakeConsultaForoRepository,
    FakeEventoForoRepository,
    FakeForoAbogadosPort,
    FakeHistorialForoRepository,
    FakeRegistroForoRepository,
    FakeRegistroForoVersionRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_RULE_ENGINE = cargar_rule_engine_foro()


def _reglas_cache_siempre_vigente() -> RuleEngineForo:
    return RuleEngineForo(campos=_RULE_ENGINE.campos, cache=ReglasCacheForo(dias_vigencia=30), circuito=_RULE_ENGINE.circuito)


def _pm() -> PersonaMaster:
    return PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"), id=1)


def _persona() -> Persona:
    return Persona(nombre_completo=NombreCompleto("Juan", "Perez"), cedula="0999999999", id=1, fingerprint="JUANPEREZ")


def _servicio(foro_port: FakeForoAbogadosPort, reglas: RuleEngineForo | None = None):
    consulta_repo = FakeConsultaForoRepository()
    registro_repo = FakeRegistroForoRepository()
    version_repo = FakeRegistroForoVersionRepository()
    historial_repo = FakeHistorialForoRepository()
    alerta_repo = FakeAlertaForoRepository()
    evento_repo = FakeEventoForoRepository()

    servicio = EnriquecimientoForoService(
        cache_service=CacheForoService(consulta_repo, (reglas or _reglas_cache_siempre_vigente()).cache),
        foro_port=foro_port,
        consulta_service=ConsultaForoService(consulta_repo, ahora_provider=lambda: _AHORA),
        comparacion_service=ComparacionForoService(registro_repo),
        registro_service=RegistroForoService(registro_repo, version_repo, historial_repo),
        alerta_service=AlertaForoService(alerta_repo),
        evento_service=EventoForoService(evento_repo),
        rule_engine_foro=reglas or _reglas_cache_siempre_vigente(),
        ahora_provider=lambda: _AHORA,
    )
    return servicio, consulta_repo, registro_repo, alerta_repo, evento_repo


class TestEnriquecer:
    def test_primer_registro_encontrado_es_dato_nuevo(self) -> None:
        foro = FakeForoAbogadosPort([[RegistroForoDTO(nombre_completo="Juan Perez", registro="R1", provincia="Pichincha")]])
        servicio, consulta_repo, registro_repo, alerta_repo, _evento_repo = _servicio(foro)

        resultado = servicio.enriquecer(_pm(), _persona())

        assert resultado.consultado is True
        assert resultado.registros_nuevos == 1
        assert resultado.cambios_detectados == 1
        assert len(registro_repo.guardados) == 1
        assert len(alerta_repo.guardadas) == 1
        assert len(consulta_repo.guardadas) == 1
        assert consulta_repo.guardadas[0].exito is True

    def test_segunda_consulta_dentro_de_vigencia_se_omite_por_cache(self) -> None:
        foro = FakeForoAbogadosPort([[RegistroForoDTO(registro="R1")]])
        servicio, *_ = _servicio(foro)
        pm = _pm()
        persona = _persona()
        servicio.enriquecer(pm, persona)
        resultado_2 = servicio.enriquecer(pm, persona)

        assert resultado_2.consultado is False
        assert foro.llamadas == 1

    def test_falla_del_foro_registra_error_y_evento_fallido(self) -> None:
        foro = FakeForoAbogadosPort(error=ConsultaForoFallidaError("timeout"))
        servicio, consulta_repo, _registro_repo, _alerta_repo, evento_repo = _servicio(foro)

        resultado = servicio.enriquecer(_pm(), _persona())

        assert resultado.error == "timeout"
        assert consulta_repo.guardadas[0].exito is False
        assert len(evento_repo.guardados) == 1

    def test_sin_cambios_entre_dos_consultas_no_genera_alertas_nuevas(self) -> None:
        registro = RegistroForoDTO(registro="R1", provincia="Pichincha", estado="Vigente")
        foro = FakeForoAbogadosPort([[registro], [registro]])
        servicio, consulta_repo, _registro_repo, alerta_repo, _evento_repo = _servicio(foro)
        pm = _pm()
        persona = _persona()

        servicio.enriquecer(pm, persona)
        consulta_repo.guardadas.clear()  # forzar que el cache permita la segunda consulta
        resultado_2 = servicio.enriquecer(pm, persona)

        assert resultado_2.cambios_detectados == 0
        assert len(alerta_repo.guardadas) == 1  # solo de la primera consulta

    def test_cambio_de_estado_genera_alerta(self) -> None:
        v1 = RegistroForoDTO(registro="R1", provincia="Pichincha", estado="Vigente")
        v2 = RegistroForoDTO(registro="R1", provincia="Pichincha", estado="Suspendido")
        foro = FakeForoAbogadosPort([[v1], [v2]])
        servicio, consulta_repo, _registro_repo, alerta_repo, _evento_repo = _servicio(foro)
        pm = _pm()
        persona = _persona()

        servicio.enriquecer(pm, persona)
        consulta_repo.guardadas.clear()
        resultado_2 = servicio.enriquecer(pm, persona)

        assert resultado_2.cambios_detectados == 1
        tipos_alerta = {a.tipo.value for a in alerta_repo.guardadas}
        assert "cambio_estado" in tipos_alerta

    def test_registro_desaparecido_es_dato_eliminado(self) -> None:
        foro = FakeForoAbogadosPort([[RegistroForoDTO(registro="R1")], []])
        servicio, consulta_repo, _registro_repo, _alerta_repo, _evento_repo = _servicio(foro)
        pm = _pm()
        persona = _persona()

        servicio.enriquecer(pm, persona)
        consulta_repo.guardadas.clear()
        resultado_2 = servicio.enriquecer(pm, persona)

        assert resultado_2.registros_eliminados == 1
