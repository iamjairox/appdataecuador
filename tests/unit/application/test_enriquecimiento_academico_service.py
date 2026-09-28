"""Tests: EnriquecimientoAcademicoService -- EL PIPELINE del Modulo 7."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.application.services.alerta_academica_service import AlertaAcademicaService
from govdata.application.services.cache_senescyt_service import CacheSenescytService
from govdata.application.services.comparacion_academica_service import ComparacionAcademicaService
from govdata.application.services.consulta_senescyt_service import ConsultaSenescytService
from govdata.application.services.enriquecimiento_academico_service import (
    EnriquecimientoAcademicoService,
)
from govdata.application.services.evento_academico_service import EventoAcademicoService
from govdata.application.services.titulo_academico_service import TituloAcademicoService
from govdata.config.rule_engine_academico import cargar_rule_engine_academico
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import ConsultaSenescytFallidaError
from govdata.domain.rules.reglas_academicas import ReglasCacheSenescyt, RuleEngineAcademico
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes_modulo7 import (
    FakeAlertaAcademicaRepository,
    FakeConsultaSenescytRepository,
    FakeEventoAcademicoRepository,
    FakeHistorialAcademicoRepository,
    FakeSenescytPort,
    FakeTituloAcademicoRepository,
    FakeTituloVersionRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_RULE_ENGINE = cargar_rule_engine_academico()


def _reglas_sin_catalogos() -> RuleEngineAcademico:
    # reutiliza los catalogos reales (titulos/universidades/niveles) pero
    # con cache siempre vigente (30 dias) por defecto
    return RuleEngineAcademico(
        titulos=_RULE_ENGINE.titulos, universidades=_RULE_ENGINE.universidades, niveles=_RULE_ENGINE.niveles,
        cache=ReglasCacheSenescyt(dias_vigencia=30),
    )


def _pm() -> PersonaMaster:
    return PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"), id=1)


def _senales() -> SenalesIdentidadDTO:
    return SenalesIdentidadDTO(nombre="Juan", apellido="Perez")


def _servicio(senescyt_port: FakeSenescytPort, reglas: RuleEngineAcademico | None = None):
    consulta_repo = FakeConsultaSenescytRepository()
    titulo_repo = FakeTituloAcademicoRepository()
    version_repo = FakeTituloVersionRepository()
    historial_repo = FakeHistorialAcademicoRepository()
    alerta_repo = FakeAlertaAcademicaRepository()
    evento_repo = FakeEventoAcademicoRepository()

    servicio = EnriquecimientoAcademicoService(
        cache_service=CacheSenescytService(consulta_repo, (reglas or _reglas_sin_catalogos()).cache),
        senescyt_port=senescyt_port,
        consulta_service=ConsultaSenescytService(consulta_repo, ahora_provider=lambda: _AHORA),
        comparacion_service=ComparacionAcademicaService(titulo_repo),
        titulo_service=TituloAcademicoService(titulo_repo, version_repo, historial_repo),
        alerta_service=AlertaAcademicaService(alerta_repo),
        evento_service=EventoAcademicoService(evento_repo),
        rule_engine_academico=reglas or _reglas_sin_catalogos(),
        ahora_provider=lambda: _AHORA,
    )
    return servicio, consulta_repo, titulo_repo, alerta_repo, evento_repo


class TestEnriquecer:
    def test_primera_consulta_registra_titulo_nuevo(self) -> None:
        senescyt = FakeSenescytPort(
            [[PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro="R1")]]
        )
        servicio, consulta_repo, titulo_repo, alerta_repo, _evento_repo = _servicio(senescyt)

        resultado = servicio.enriquecer(_pm(), _senales())

        assert resultado.consultado is True
        assert resultado.titulos_nuevos == 1
        assert resultado.cambios_detectados == 1
        assert len(titulo_repo.guardados) == 1
        assert len(alerta_repo.guardadas) == 1  # NUEVO_TITULO
        assert len(consulta_repo.guardadas) == 1
        assert consulta_repo.guardadas[0].exito is True

    def test_segunda_consulta_dentro_de_vigencia_se_omite_por_cache(self) -> None:
        senescyt = FakeSenescytPort(
            [[PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro="R1")]]
        )
        servicio, *_ = _servicio(senescyt)
        pm = _pm()
        servicio.enriquecer(pm, _senales())
        resultado_2 = servicio.enriquecer(pm, _senales())

        assert resultado_2.consultado is False
        assert senescyt.llamadas == 1

    def test_falla_de_senescyt_registra_error_y_evento_fallido(self) -> None:
        senescyt = FakeSenescytPort(error=ConsultaSenescytFallidaError("timeout"))
        servicio, consulta_repo, _titulo_repo, _alerta_repo, evento_repo = _servicio(senescyt)

        resultado = servicio.enriquecer(_pm(), _senales())

        assert resultado.error == "timeout"
        assert consulta_repo.guardadas[0].exito is False
        assert len(evento_repo.guardados) == 1

    def test_sin_cambios_entre_dos_consultas_no_genera_alertas(self) -> None:
        titulo = PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro="R1")
        senescyt = FakeSenescytPort([[titulo], [titulo]])
        servicio, consulta_repo, _titulo_repo, alerta_repo, _evento_repo = _servicio(senescyt)
        pm = _pm()

        servicio.enriquecer(pm, _senales())
        consulta_repo.guardadas.clear()  # forzar que el cache permita la segunda consulta
        resultado_2 = servicio.enriquecer(pm, _senales())

        assert resultado_2.cambios_detectados == 0
        assert len(alerta_repo.guardadas) == 1  # solo de la primera consulta

    def test_cambio_de_estado_a_suspendido_genera_alerta_critica(self) -> None:
        v1 = PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro="R1", estado="Vigente")
        v2 = PersonaAcademicaDTO(titulo="Abogado", nivel="Tercer Nivel", institucion="UCE", numero_registro="R1", estado="Suspendido")
        senescyt = FakeSenescytPort([[v1], [v2]])
        servicio, consulta_repo, _titulo_repo, alerta_repo, _evento_repo = _servicio(senescyt)
        pm = _pm()

        servicio.enriquecer(pm, _senales())
        consulta_repo.guardadas.clear()
        resultado_2 = servicio.enriquecer(pm, _senales())

        assert resultado_2.cambios_detectados == 1
        tipos_alerta = {a.tipo.value for a in alerta_repo.guardadas}
        assert "registro_suspendido" in tipos_alerta
