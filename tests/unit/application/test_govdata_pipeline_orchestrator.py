"""Tests: GovDataPipelineOrchestrator -- Submodulo 9.1, EL UNICO PUNTO DE
ENTRADA del sistema. Colaboradores pesados de Modulos 5/6/7/8 (REUTILIZADOS)
se duplican via `fakes_orquestador_pipeline.py`; los repositorios de
Entidad/Funcionario/Persona reutilizan los fakes YA EXISTENTES de otros
modulos (`fakes.py`/`fakes_extraccion.py`); la cola/auditoria usan los
SERVICIOS REALES (`ColaTrabajosOrquestadorService`/`AuditoriaOrquestacionService`)
sobre los fakes de repositorio del propio Modulo 9 (`fakes_modulo9.py`) --
asi se prueba la logica REAL de estado/bloqueo-optimista/auditoria, solo
faltando la capa SQL."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest

from govdata.application.dto.filtros_consulta_dto import FiltrosConsultaDTO
from govdata.application.dto.resultado_orquestacion_dto import ResultadoOrquestacionDTO
from govdata.application.ports.funcionario_repository_port import FuncionarioRepositoryPort
from govdata.application.services.auditoria_orquestacion_service import AuditoriaOrquestacionService
from govdata.application.services.cola_trabajos_orquestador_service import (
    ColaTrabajosOrquestadorService,
)
from govdata.application.services.govdata_pipeline_orchestrator import GovDataPipelineOrchestrator
from govdata.application.services.motor_politicas_service import MotorPoliticasService
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import EntidadNoEncontradaError, GovDataError
from govdata.domain.rules.reglas_orquestador import CatalogoPoliticas, PoliticaEjecucion
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.cargo import Cargo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador
from tests.unit.application.fakes import FakeEntidadRepository
from tests.unit.application.fakes_extraccion import (
    FakeFuncionarioRepositoryExtraccion,
    FakePersonaRepository,
)
from tests.unit.application.fakes_modulo9 import (
    FakeAuditoriaEtapaRepository,
    FakeTrabajoOrquestadorRepository,
)
from tests.unit.application.fakes_orquestador_pipeline import (
    FakeEnriquecimientoAcademicoService,
    FakeEnriquecimientoForoService,
    FakeMonitoreoContinuoService,
    FakePerfilConsolidadoService,
    FakeResolverPersonaMasterUseCase,
    construir_resultado_monitoreo,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _catalogo_politicas() -> CatalogoPoliticas:
    """Mismos 4 nombres/valores que `config/rules/politicas_ejecucion.yaml`."""
    return CatalogoPoliticas(
        politicas_por_nombre={
            "consulta_rapida": PoliticaEjecucion(nombre="consulta_rapida", usar_cache=True, concurrencia_maxima=1),
            "actualizacion_completa": PoliticaEjecucion(
                nombre="actualizacion_completa", usar_cache=False, forzar_actualizacion=True, concurrencia_maxima=1,
            ),
            "solo_cambios": PoliticaEjecucion(nombre="solo_cambios", solo_cambios=True, concurrencia_maxima=2),
            "masiva_nocturna": PoliticaEjecucion(
                nombre="masiva_nocturna", concurrencia_maxima=5, reintentos_automaticos=True, prioridad_pendientes=True,
            ),
        }
    )


@dataclass
class _Entorno:
    orquestador: GovDataPipelineOrchestrator
    entidad_repo: FakeEntidadRepository
    funcionario_repo: FakeFuncionarioRepositoryExtraccion
    persona_repo: FakePersonaRepository
    monitoreo: FakeMonitoreoContinuoService
    resolver: FakeResolverPersonaMasterUseCase
    perfil: FakePerfilConsolidadoService
    enriq_academico: FakeEnriquecimientoAcademicoService
    enriq_foro: FakeEnriquecimientoForoService
    cola: ColaTrabajosOrquestadorService
    auditoria_repo: FakeAuditoriaEtapaRepository
    llamadas_politica_academico: list[PoliticaEjecucion]
    llamadas_politica_foro: list[PoliticaEjecucion]


def _construir_entorno(
    ejecutor_aislado: Callable[[str, TipoTrabajoOrquestador, str], ResultadoOrquestacionDTO] | None = None,
    funcionario_repo: FakeFuncionarioRepositoryExtraccion | Any | None = None,
    personas_con_error: set[int] | None = None,
) -> _Entorno:
    entidad_repo = FakeEntidadRepository()
    funcionario_repo = funcionario_repo if funcionario_repo is not None else FakeFuncionarioRepositoryExtraccion()
    persona_repo = FakePersonaRepository()
    monitoreo = FakeMonitoreoContinuoService()
    resolver = FakeResolverPersonaMasterUseCase(personas_con_error=personas_con_error)
    perfil = FakePerfilConsolidadoService()
    enriq_academico = FakeEnriquecimientoAcademicoService()
    enriq_foro = FakeEnriquecimientoForoService()

    llamadas_politica_academico: list[PoliticaEjecucion] = []
    llamadas_politica_foro: list[PoliticaEjecucion] = []

    def _crear_academico(politica: PoliticaEjecucion) -> FakeEnriquecimientoAcademicoService:
        llamadas_politica_academico.append(politica)
        return enriq_academico

    def _crear_foro(politica: PoliticaEjecucion) -> FakeEnriquecimientoForoService:
        llamadas_politica_foro.append(politica)
        return enriq_foro

    cola = ColaTrabajosOrquestadorService(FakeTrabajoOrquestadorRepository(), ahora_provider=lambda: _AHORA)
    auditoria_repo = FakeAuditoriaEtapaRepository()
    auditoria = AuditoriaOrquestacionService(auditoria_repo)
    motor_politicas = MotorPoliticasService(_catalogo_politicas())

    orquestador = GovDataPipelineOrchestrator(
        entidad_repository=entidad_repo,
        funcionario_repository=funcionario_repo,
        persona_repository=persona_repo,
        monitoreo_service=monitoreo,  # type: ignore[arg-type]
        resolver_persona_master_use_case=resolver,  # type: ignore[arg-type]
        perfil_consolidado_service=perfil,  # type: ignore[arg-type]
        crear_enriquecimiento_academico=_crear_academico,  # type: ignore[arg-type]
        crear_enriquecimiento_foro=_crear_foro,  # type: ignore[arg-type]
        motor_politicas=motor_politicas,
        cola=cola,
        auditoria=auditoria,
        ahora_provider=lambda: _AHORA,
        ejecutor_aislado=ejecutor_aislado,
    )
    return _Entorno(
        orquestador=orquestador, entidad_repo=entidad_repo, funcionario_repo=funcionario_repo, persona_repo=persona_repo,
        monitoreo=monitoreo, resolver=resolver, perfil=perfil, enriq_academico=enriq_academico, enriq_foro=enriq_foro,
        cola=cola, auditoria_repo=auditoria_repo,
        llamadas_politica_academico=llamadas_politica_academico, llamadas_politica_foro=llamadas_politica_foro,
    )


def _entidad(entidad_repo: FakeEntidadRepository, nombre: str = "Procuraduria General del Estado") -> Entidad:
    return entidad_repo.guardar_o_actualizar(Entidad(nombre=nombre, url_transparencia=f"https://x.test/{nombre}", portal_origen="dpe"))


def _funcionario_juridico(
    env: _Entorno, entidad: Entidad, nombres: str = "Ana", apellidos: str = "Torres", cedula: str = "0102030405",
) -> Funcionario:
    persona = env.persona_repo.guardar(Persona(nombre_completo=NombreCompleto(nombres, apellidos), cedula=cedula))
    assert persona.id is not None
    return env.funcionario_repo.guardar(
        Funcionario(
            persona_id=persona.id, entidad_id=entidad.id, cargo=Cargo("Procurador"),
            dependencia="Direccion Juridica", area_clasificada=AreaRelevante.JURIDICA,
        )
    )


class _FuncionarioRepoQueFalla(FuncionarioRepositoryPort):
    """Simula un fallo de infraestructura (ej. timeout de BD) al listar
    funcionarios de una entidad -- para probar que
    `_ejecutar_con_trabajo_existente` marca el trabajo en ERROR y
    RE-LANZA (en vez de tragarse el error silenciosamente)."""

    def guardar(self, funcionario: Funcionario) -> Funcionario:
        raise NotImplementedError

    def guardar_lote(self, funcionarios: list[Funcionario]) -> list[Funcionario]:
        raise NotImplementedError

    def buscar_vigente(self, persona_id: int, entidad_id: int) -> Funcionario | None:
        raise NotImplementedError

    def listar_por_entidad(self, entidad_id: int, solo_vigentes: bool = True) -> list[Funcionario]:
        raise GovDataError("timeout de base de datos")

    def listar_por_documento(self, documento_id: int) -> list[Funcionario]:
        raise NotImplementedError

    def buscar_con_filtros(self, filtros: FiltrosConsultaDTO) -> list[Funcionario]:
        raise NotImplementedError


class TestContratoOficial:
    def test_contrato_9_14_shape_happy_path(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        _funcionario_juridico(env, entidad)
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )
        env.enriq_academico.cambios_detectados = 2
        env.perfil._mapa = {
            1: [{"registro": "12345", "estado": "Activo", "provincia": "Pichincha", "fecha_consulta": _AHORA}],
        }

        resultado = env.orquestador.consultar_entidad(entidad.nombre)

        assert isinstance(resultado, ResultadoOrquestacionDTO)
        assert set(resultado.to_dict()) == {
            "job", "entidad", "estadisticas", "funcionarios", "alertas", "errores", "duracion_total", "generado_en",
        }
        assert resultado.job["estado"] == "completado"
        assert resultado.job["politica"] == "consulta_rapida"
        assert resultado.entidad == {"id": entidad.id, "nombre": entidad.nombre}
        assert resultado.estadisticas["funcionarios_juridicos"] == 1
        assert resultado.estadisticas["consultas_senescyt"] == 1
        assert resultado.estadisticas["consultas_foro"] == 1
        assert resultado.estadisticas["cache_hit"] == 0
        assert resultado.estadisticas["cache_miss"] == 2
        assert resultado.estadisticas["cambios_detectados"] == 2
        assert resultado.errores == []
        assert len(resultado.funcionarios) == 1
        funcionario_dto = resultado.funcionarios[0]
        assert funcionario_dto["cedula"] == "0102030405"
        assert funcionario_dto["registro_foro"] == "12345"
        assert funcionario_dto["estado_foro"] == "Activo"
        assert funcionario_dto["fecha_consulta"] == _AHORA.isoformat()
        assert resultado.duracion_total.endswith("s")

    def test_entidad_no_encontrada_lanza_error(self) -> None:
        env = _construir_entorno()
        with pytest.raises(EntidadNoEncontradaError):
            env.orquestador.consultar_entidad("No Existe")


class TestPoliticaSoloCambios:
    def test_sin_novedad_omite_senescyt_foro_perfil_alertas(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        _funcionario_juridico(env, entidad)
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, False, "hash_remoto_sin_cambios", _AHORA,
        )

        resultado = env.orquestador.consultar_entidad(entidad.nombre, politica="solo_cambios")

        assert resultado.funcionarios == []
        assert resultado.estadisticas["consultas_senescyt"] == 0
        assert resultado.estadisticas["consultas_foro"] == 0
        assert env.enriq_academico.llamadas == []
        assert env.enriq_foro.llamadas == []

        etapas = {e.tipo_paso: e for e in env.auditoria_repo.guardadas if e.trabajo_orquestador_id == resultado.job["id"]}
        for paso in (TipoPasoPipeline.SENESCYT, TipoPasoPipeline.FORO, TipoPasoPipeline.PERFIL, TipoPasoPipeline.ALERTAS):
            assert etapas[paso].razon_omision == "politica_solo_cambios_sin_novedad"


class TestActualizarEntidad:
    def test_fuerza_politica_actualizacion_completa(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )

        resultado = env.orquestador.actualizar_entidad(entidad.nombre)

        assert resultado.job["politica"] == "actualizacion_completa"
        assert resultado.job["tipo"] == "actualizacion_entidad"


class TestPipelineParcial:
    def test_solo_senescyt_omite_transparencia_foro_perfil_alertas(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        _funcionario_juridico(env, entidad)

        resultado = env.orquestador.consultar_entidad(
            entidad.nombre, pasos=frozenset({TipoPasoPipeline.SENESCYT}),
        )

        assert env.monitoreo.llamadas == []
        assert env.enriq_academico.llamadas == [1]
        assert env.enriq_foro.llamadas == []
        assert resultado.estadisticas["consultas_senescyt"] == 1
        assert resultado.estadisticas["consultas_foro"] == 0

        etapas = {e.tipo_paso: e for e in env.auditoria_repo.guardadas if e.trabajo_orquestador_id == resultado.job["id"]}
        for paso in (TipoPasoPipeline.DESCUBRIMIENTO, TipoPasoPipeline.DESCARGA, TipoPasoPipeline.EXTRACCION, TipoPasoPipeline.FORO, TipoPasoPipeline.PERFIL, TipoPasoPipeline.ALERTAS):
            assert etapas[paso].razon_omision == "pipeline_parcial_no_solicitado"


class TestReprocesarJob:
    def test_reprocesa_trabajo_en_error_con_los_mismos_parametros(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )

        trabajo = env.cola.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": entidad.nombre}, "consulta_rapida")
        env.cola.iniciar_directo(trabajo)
        env.cola.marcar_error(trabajo, "fallo transitorio")

        resultado = env.orquestador.reprocesar_job(trabajo.id)

        assert resultado.errores == []
        assert resultado.job["estado"] == "completado"
        assert resultado.job["id"] == str(trabajo.id)

    def test_job_inexistente_lanza_error(self) -> None:
        import uuid

        env = _construir_entorno()
        with pytest.raises(EntidadNoEncontradaError):
            env.orquestador.reprocesar_job(uuid.uuid4())


class TestConsultaPorFiltro:
    def test_resuelve_entidades_desde_funcionarios_filtrados(self) -> None:
        env = _construir_entorno()
        entidad_a = _entidad(env.entidad_repo, "Entidad A")
        entidad_b = _entidad(env.entidad_repo, "Entidad B")
        assert entidad_a.id is not None
        assert entidad_b.id is not None
        _funcionario_juridico(env, entidad_a, cedula="1111111111")
        _funcionario_juridico(env, entidad_b, cedula="2222222222")
        for entidad in (entidad_a, entidad_b):
            env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
                entidad.id, True, "cambios_detectados", _AHORA,
            )

        filtros = FiltrosConsultaDTO(area=AreaRelevante.JURIDICA)
        resultados = env.orquestador.consultar_por_filtro(filtros)

        nombres_procesados = {r.entidad["nombre"] for r in resultados}
        assert nombres_procesados == {"Entidad A", "Entidad B"}


class TestConsultarMasivoSecuencial:
    def test_procesa_todas_las_entidades_activas_en_orden(self) -> None:
        env = _construir_entorno()
        entidad_a = _entidad(env.entidad_repo, "Entidad A")
        entidad_b = _entidad(env.entidad_repo, "Entidad B")
        assert entidad_a.id is not None
        assert entidad_b.id is not None
        for entidad in (entidad_a, entidad_b):
            env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
                entidad.id, True, "cambios_detectados", _AHORA,
            )

        resultados = env.orquestador.consultar_masivo()

        assert [r.entidad["nombre"] for r in resultados] == ["Entidad A", "Entidad B"]


class TestActualizarMasivoParalelo:
    def test_fuerza_politica_masiva_nocturna_y_usa_ejecutor_aislado(self) -> None:
        llamadas: list[tuple[str, TipoTrabajoOrquestador, str]] = []
        lock = threading.Lock()

        def ejecutor_aislado(nombre: str, tipo: TipoTrabajoOrquestador, politica: str) -> ResultadoOrquestacionDTO:
            with lock:
                llamadas.append((nombre, tipo, politica))
            return ResultadoOrquestacionDTO(job={"id": nombre, "estado": "completado"}, entidad={"nombre": nombre})

        env = _construir_entorno(ejecutor_aislado=ejecutor_aislado)
        nombres = [f"Entidad {i}" for i in range(5)]
        for nombre in nombres:
            _entidad(env.entidad_repo, nombre)

        resultados = env.orquestador.actualizar_masivo()

        assert {r.entidad["nombre"] for r in resultados} == set(nombres)
        assert {n for n, _tipo, _pol in llamadas} == set(nombres)
        assert all(tipo == TipoTrabajoOrquestador.ACTUALIZACION_MASIVA for _n, tipo, _pol in llamadas)
        assert all(politica == "masiva_nocturna" for _n, _tipo, politica in llamadas)

    def test_aisla_fallo_permanente_de_una_entidad_sin_afectar_al_resto(self) -> None:
        def ejecutor_aislado(nombre: str, tipo: TipoTrabajoOrquestador, politica: str) -> ResultadoOrquestacionDTO:
            if nombre == "Entidad Rota":
                raise GovDataError("fallo permanente")
            return ResultadoOrquestacionDTO(job={"id": nombre, "estado": "completado"}, entidad={"nombre": nombre})

        env = _construir_entorno(ejecutor_aislado=ejecutor_aislado)
        nombres = ["Entidad Rota", "Entidad Sana 1", "Entidad Sana 2"]
        for nombre in nombres:
            _entidad(env.entidad_repo, nombre)

        resultados = env.orquestador.actualizar_masivo()

        assert {r.entidad["nombre"] for r in resultados} == {"Entidad Sana 1", "Entidad Sana 2"}

    def test_reintenta_automaticamente_y_recupera_una_entidad_flaky(self) -> None:
        intentos: dict[str, int] = {}
        lock = threading.Lock()

        def ejecutor_aislado(nombre: str, tipo: TipoTrabajoOrquestador, politica: str) -> ResultadoOrquestacionDTO:
            with lock:
                intentos[nombre] = intentos.get(nombre, 0) + 1
                intento_actual = intentos[nombre]
            if nombre == "Entidad Flaky" and intento_actual == 1:
                raise GovDataError("fallo transitorio")
            return ResultadoOrquestacionDTO(job={"id": nombre, "estado": "completado"}, entidad={"nombre": nombre})

        env = _construir_entorno(ejecutor_aislado=ejecutor_aislado)
        _entidad(env.entidad_repo, "Entidad Flaky")

        resultados = env.orquestador.actualizar_masivo()

        assert {r.entidad["nombre"] for r in resultados} == {"Entidad Flaky"}
        assert intentos["Entidad Flaky"] == 2


class TestFactoriesReciebenLaPoliticaActiva:
    def test_crear_enriquecimiento_recibe_la_politica_resuelta(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        _funcionario_juridico(env, entidad)
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )

        env.orquestador.actualizar_entidad(entidad.nombre)

        assert len(env.llamadas_politica_academico) == 1
        assert env.llamadas_politica_academico[0].nombre == "actualizacion_completa"
        assert env.llamadas_politica_academico[0].forzar_actualizacion is True
        assert len(env.llamadas_politica_foro) == 1
        assert env.llamadas_politica_foro[0].nombre == "actualizacion_completa"


class TestReprocesarJobRamasAdicionales:
    def test_sin_nombre_entidad_en_parametros_lanza_error(self) -> None:
        env = _construir_entorno()
        trabajo = env.cola.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {}, "consulta_rapida")
        with pytest.raises(EntidadNoEncontradaError):
            env.orquestador.reprocesar_job(trabajo.id)

    def test_trabajo_pausado_se_reanuda_y_ejecuta(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )
        trabajo = env.cola.encolar(
            TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": entidad.nombre}, "consulta_rapida",
        )
        env.cola.pausar(trabajo)

        resultado = env.orquestador.reprocesar_job(trabajo.id)

        assert resultado.job["estado"] == "completado"

    def test_entidad_del_job_ya_no_existe_lanza_error(self) -> None:
        env = _construir_entorno()
        trabajo = env.cola.encolar(
            TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": "Entidad Borrada"}, "consulta_rapida",
        )
        with pytest.raises(EntidadNoEncontradaError):
            env.orquestador.reprocesar_job(trabajo.id)


class TestFalloDeTransparenciaSeRegistraSinDetenerElPipeline:
    def test_monitoreo_falla_registra_fallido_y_continua_a_senescyt_foro(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        _funcionario_juridico(env, entidad)
        env.monitoreo._entidades_con_error[entidad.nombre] = GovDataError("portal de transparencia caido")

        resultado = env.orquestador.consultar_entidad(entidad.nombre)

        assert any(e.startswith("transparencia:") for e in resultado.errores)
        assert resultado.job["estado"] == "error"
        # A pesar del fallo en Transparencia, el resto del pipeline
        # (SENESCYT/Foro sobre los funcionarios ya conocidos) SI continua
        # -- `hubo_cambio_transparencia` mantiene su valor por defecto True.
        assert env.enriq_academico.llamadas == [1]

        etapas = {e.tipo_paso: e for e in env.auditoria_repo.guardadas if e.trabajo_orquestador_id == resultado.job["id"]}
        assert etapas[TipoPasoPipeline.DESCUBRIMIENTO].estado_paso.value == "fallido"
        assert etapas[TipoPasoPipeline.DESCUBRIMIENTO].error == "portal de transparencia caido"


class TestFalloDeInfraestructuraSeRelanza:
    def test_fallo_no_gobierno_data_error_marca_error_y_relanza(self) -> None:
        env = _construir_entorno(funcionario_repo=_FuncionarioRepoQueFalla())
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )

        with pytest.raises(GovDataError):
            env.orquestador.consultar_entidad(entidad.nombre)

        trabajo_persistido = next(iter(env.cola._repository.guardados.values()))
        assert trabajo_persistido.estado.value == "error"


class TestErrorPorFuncionarioNoDetieneAlResto:
    def test_un_funcionario_irresoluble_se_reporta_sin_tumbar_a_los_demas(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        roto = _funcionario_juridico(env, entidad, nombres="Rota", apellidos="Persona", cedula="0000000001")
        _funcionario_juridico(env, entidad, nombres="Sana", apellidos="Persona", cedula="0000000002")
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )
        env.resolver._personas_con_error = {roto.persona_id}

        resultado = env.orquestador.consultar_entidad(entidad.nombre)

        assert resultado.job["estado"] == "error"
        assert len(resultado.errores) == 1
        assert len(resultado.funcionarios) == 1


class TestFuncionarioHuerfano:
    def test_funcionario_sin_persona_asociada_se_omite_silenciosamente(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        # Referencia un persona_id que NUNCA se guardo en `persona_repo`
        # (ej. la Persona fue eliminada por otra fuente).
        env.funcionario_repo.guardar(
            Funcionario(
                persona_id=999999, entidad_id=entidad.id, cargo=Cargo("Procurador"),
                dependencia="Direccion Juridica", area_clasificada=AreaRelevante.JURIDICA,
            )
        )
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )

        resultado = env.orquestador.consultar_entidad(entidad.nombre)

        assert resultado.errores == []
        assert resultado.funcionarios == []


class TestFiltroIgnoraEntidadesYaNoExistentes:
    def test_entidad_id_huerfano_no_se_resuelve(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        _funcionario_juridico(env, entidad)
        persona_fantasma = env.persona_repo.guardar(Persona(nombre_completo=NombreCompleto("Fantasma", "Entidad")))
        assert persona_fantasma.id is not None
        env.funcionario_repo.guardar(
            Funcionario(
                persona_id=persona_fantasma.id, entidad_id=99999, cargo=Cargo("Procurador"),
                dependencia="X", area_clasificada=AreaRelevante.JURIDICA,
            )
        )
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )

        resultados = env.orquestador.consultar_por_filtro(FiltrosConsultaDTO(area=AreaRelevante.JURIDICA))

        assert {r.entidad["nombre"] for r in resultados} == {entidad.nombre}


class TestPipelineParcialSoloForo:
    def test_solo_foro_omite_senescyt(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        _funcionario_juridico(env, entidad)

        resultado = env.orquestador.consultar_entidad(entidad.nombre, pasos=frozenset({TipoPasoPipeline.FORO}))

        assert env.enriq_academico.llamadas == []
        assert env.enriq_foro.llamadas == [1]

        etapas = {e.tipo_paso: e for e in env.auditoria_repo.guardadas if e.trabajo_orquestador_id == resultado.job["id"]}
        assert etapas[TipoPasoPipeline.SENESCYT].razon_omision == "pipeline_parcial_no_solicitado"


class TestCacheHitCuandoRespuestaVieneDelCache:
    def test_academico_y_foro_desde_cache_cuentan_como_cache_hit(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        _funcionario_juridico(env, entidad)
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )
        env.enriq_academico.consultado = False
        env.enriq_foro.consultado = False

        resultado = env.orquestador.consultar_entidad(entidad.nombre)

        assert resultado.estadisticas["cache_hit"] == 2
        assert resultado.estadisticas["cache_miss"] == 0
        assert resultado.estadisticas["consultas_senescyt"] == 0
        assert resultado.estadisticas["consultas_foro"] == 0


class TestLoteVacioYFalloSecuencialSinReintento:
    def test_lote_sin_entidades_retorna_lista_vacia(self) -> None:
        env = _construir_entorno()
        assert env.orquestador.consultar_masivo() == []

    def test_fallo_secuencial_sin_reintentos_automaticos_se_omite_del_resultado(self) -> None:
        # "consulta_rapida" (concurrencia_maxima=1, reintentos_automaticos=False):
        # camino SECUENCIAL puro (sin `ejecutor_aislado`). Un nombre de
        # entidad que nunca existio (ej. borrada entre listar y ejecutar)
        # produce un fallo que NO se reintenta y se omite silenciosamente
        # del lote, sin tumbar a las demas.
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo, "Entidad Real")
        assert entidad.id is not None
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )

        resultados = env.orquestador._ejecutar_lote(
            ["Entidad Fantasma", "Entidad Real"], TipoTrabajoOrquestador.CONSULTA_MASIVA, "consulta_rapida",
        )

        assert [r.entidad["nombre"] for r in resultados] == ["Entidad Real"]


class TestCierreDelMonitoreoYAislamientoDeHilo:
    """FASE 3.8 -- regresion del bug real reproducido contra el portal DPE
    (`Error: It looks like you are using Playwright Sync API inside the
    asyncio loop`, primera consulta 200 OK, segunda consulta ~7s despues
    500 en <1s). Causa raiz confirmada leyendo la cadena de llamadas real:
    `MonitoreoContinuoService` (dueno del navegador Playwright del paso
    Descubrimiento) nunca se cerraba tras una consulta, y el pipeline
    corria en el hilo que FastAPI/anyio decidiera asignar -- un pool que
    SE REUTILIZA entre peticiones HTTP distintas. Estos tests verifican,
    sin Playwright real, las dos propiedades que corrigen la causa raiz."""

    def test_cerrar_se_invoca_tras_una_consulta_exitosa(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )

        env.orquestador.consultar_entidad(entidad.nombre)

        assert env.monitoreo.veces_cerrado == 1

    def test_cerrar_se_invoca_incluso_si_el_pipeline_falla(self) -> None:
        env = _construir_entorno(funcionario_repo=_FuncionarioRepoQueFalla())
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )

        with pytest.raises(GovDataError):
            env.orquestador.consultar_entidad(entidad.nombre)

        assert env.monitoreo.veces_cerrado == 1

    def test_el_pipeline_corre_en_un_hilo_dedicado_distinto_al_llamador(self) -> None:
        env = _construir_entorno()
        entidad = _entidad(env.entidad_repo)
        assert entidad.id is not None
        env.monitoreo._resultado_por_entidad[entidad.nombre] = construir_resultado_monitoreo(
            entidad.id, True, "cambios_detectados", _AHORA,
        )

        env.orquestador.consultar_entidad(entidad.nombre)

        assert len(env.monitoreo.hilos_de_llamada) == 1
        assert env.monitoreo.hilos_de_llamada[0] != threading.get_ident(), (
            "el pipeline debe ejecutarse en un hilo dedicado, nunca en el hilo que llamo a consultar_entidad "
            "-- asi se evita que el pool de anyio reutilice, en otra peticion, un hilo ya usado por Playwright"
        )

    def test_dos_consultas_secuenciales_usan_hilos_distintos(self) -> None:
        """Reproduce, sin Playwright, la condicion exacta del bug real:
        si dos consultas seguidas compartieran el mismo hilo del sistema
        operativo, la Sync API de Playwright fallaria en la segunda. Con
        un hilo dedicado y descartable por llamada, nunca deben coincidir."""
        env = _construir_entorno()
        entidad_a = _entidad(env.entidad_repo, "Entidad A")
        entidad_b = _entidad(env.entidad_repo, "Entidad B")
        assert entidad_a.id is not None
        assert entidad_b.id is not None
        env.monitoreo._resultado_por_entidad[entidad_a.nombre] = construir_resultado_monitoreo(
            entidad_a.id, True, "cambios_detectados", _AHORA,
        )
        env.monitoreo._resultado_por_entidad[entidad_b.nombre] = construir_resultado_monitoreo(
            entidad_b.id, True, "cambios_detectados", _AHORA,
        )

        env.orquestador.consultar_entidad(entidad_a.nombre)
        env.orquestador.consultar_entidad(entidad_b.nombre)

        assert len(env.monitoreo.hilos_de_llamada) == 2
        assert env.monitoreo.hilos_de_llamada[0] != env.monitoreo.hilos_de_llamada[1]
