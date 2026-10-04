"""Servicio: GovDataPipelineOrchestrator -- Submodulo 9.1, EL UNICO PUNTO
DE ENTRADA del sistema GovData completo.

"El usuario nunca volvera a pensar en Transparencia, SENESCYT o Foro.
Solo pedira informacion de una entidad." Este orquestador COMPONE (nunca
reimplementa) todo lo que los Modulos 1-8 ya construyeron:

    Pasos 1-3 (Descubrimiento/Descarga/Extraccion) -> `MonitoreoContinuoService`
                                                        (Modulo 5, REUTILIZADO)
    Paso 4 (SENESCYT)                              -> `EnriquecimientoAcademicoService`
                                                        (Modulo 7, REUTILIZADO)
    Paso 5 (Foro)                                  -> `EnriquecimientoForoService`
                                                        (Modulo 8, REUTILIZADO)
    Paso 6 (Comparacion)                           -> interno a los pasos 1-5
    Paso 7 (Perfil)                                -> `PerfilConsolidadoService`
                                                        (Modulo 8, REUTILIZADO)
    Paso 8 (Alertas)                               -> interno a los pasos 1-5

Truco de diseno para el Motor de Politicas (`forzar_actualizacion`): NO
existe forma de decirle a `EnriquecimientoAcademicoService`/
`EnriquecimientoForoService` (ambos congelados) "ignora tu cache" -- pero
SI se les puede INYECTAR, al construirlos, una `ReglasCacheSenescyt`/
`ReglasCacheForo` con `dias_vigencia=0`: `debe_consultar()` (logica
interna intacta, nunca tocada) da `True` siempre, sin haber modificado
una sola linea de Modulo 7/8. `crear_enriquecimiento_academico`/
`crear_enriquecimiento_foro` son las factories (inyectadas por
`Container`) que aplican este truco segun la `PoliticaEjecucion` activa.

Concurrencia real (Submodulos 9.5/9.6/9.8, consultar_masivo/
actualizar_masivo): mismo patron `queue.Queue` + `threading.Thread` que
`DescargaOrchestratorService` (Modulo 3) -- pero, a diferencia de ese
Modulo (donde el recurso compartido era una `requests.Session`, segura de
reabrir por hilo), aqui cada ITEM individual necesita su PROPIA
transaccion de base de datos, para que el fallo de una entidad nunca
arrastre el rollback de las demas ya confirmadas. Por eso `ejecutor_aislado`
(inyectado por `Container`) no es "una fabrica de un orquestador por
hilo" sino una funcion que abre y cierra su PROPIA `Session` de
SQLAlchemy en CADA llamada -- una por entidad, sin importar cuantos hilos
la compartan concurrentemente."""

from __future__ import annotations

import concurrent.futures
import queue
import threading
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from govdata.application.dto.estadisticas_orquestacion_dto import EstadisticasOrquestacionDTO
from govdata.application.dto.filtros_consulta_dto import FiltrosConsultaDTO
from govdata.application.dto.funcionario_consolidado_dto import FuncionarioConsolidadoDTO
from govdata.application.dto.resultado_orquestacion_dto import ResultadoOrquestacionDTO
from govdata.application.dto.trabajo_orquestador_dto import TrabajoOrquestadorDTO
from govdata.application.ports.entidad_repository_port import EntidadRepositoryPort
from govdata.application.ports.funcionario_repository_port import FuncionarioRepositoryPort
from govdata.application.ports.persona_repository_port import PersonaRepositoryPort
from govdata.application.services.auditoria_orquestacion_service import AuditoriaOrquestacionService
from govdata.application.services.cola_trabajos_orquestador_service import (
    ColaTrabajosOrquestadorService,
)
from govdata.application.services.enriquecimiento_academico_service import (
    EnriquecimientoAcademicoService,
)
from govdata.application.services.enriquecimiento_foro_service import EnriquecimientoForoService
from govdata.application.services.identity_resolution_service import senales_desde_persona_master
from govdata.application.services.monitoreo_continuo_service import MonitoreoContinuoService
from govdata.application.services.motor_politicas_service import MotorPoliticasService
from govdata.application.services.perfil_consolidado_service import PerfilConsolidadoService
from govdata.application.use_cases.resolver_o_crear_persona_master_use_case import (
    ResolverOCrearPersonaMasterUseCase,
)
from govdata.config.logging_config import get_logger
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.trabajo_orquestador import TrabajoOrquestador
from govdata.domain.exceptions.domain_exceptions import (
    EntidadNoEncontradaError,
    GovDataError,
    OrquestacionFallidaError,
)
from govdata.domain.rules.reglas_orquestador import PoliticaEjecucion
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.estado_trabajo_orquestador import EstadoTrabajoOrquestador
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador

logger = get_logger(__name__)

_SENTINEL_FIN = None


class GovDataPipelineOrchestrator:
    def __init__(
        self,
        entidad_repository: EntidadRepositoryPort,
        funcionario_repository: FuncionarioRepositoryPort,
        persona_repository: PersonaRepositoryPort,
        monitoreo_service: MonitoreoContinuoService,
        resolver_persona_master_use_case: ResolverOCrearPersonaMasterUseCase,
        perfil_consolidado_service: PerfilConsolidadoService,
        crear_enriquecimiento_academico: Callable[[PoliticaEjecucion], EnriquecimientoAcademicoService],
        crear_enriquecimiento_foro: Callable[[PoliticaEjecucion], EnriquecimientoForoService],
        motor_politicas: MotorPoliticasService,
        cola: ColaTrabajosOrquestadorService,
        auditoria: AuditoriaOrquestacionService,
        politica_defecto: str = "consulta_rapida",
        ahora_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
        ejecutor_aislado: Callable[[str, TipoTrabajoOrquestador, str], ResultadoOrquestacionDTO] | None = None,
    ) -> None:
        self._entidad_repository = entidad_repository
        self._funcionario_repository = funcionario_repository
        self._persona_repository = persona_repository
        self._monitoreo_service = monitoreo_service
        self._resolver_persona_master_use_case = resolver_persona_master_use_case
        self._perfil_consolidado_service = perfil_consolidado_service
        self._crear_enriquecimiento_academico = crear_enriquecimiento_academico
        self._crear_enriquecimiento_foro = crear_enriquecimiento_foro
        self._motor_politicas = motor_politicas
        self._cola = cola
        self._auditoria = auditoria
        self._politica_defecto = politica_defecto
        self._ahora_provider = ahora_provider
        self._ejecutor_aislado = ejecutor_aislado

    # -- Submodulo 9.1: metodos minimos ----------------------------------

    def consultar_entidad(
        self, nombre_entidad: str, politica: str | None = None, pasos: frozenset[TipoPasoPipeline] | None = None,
    ) -> ResultadoOrquestacionDTO:
        return self._ejecutar_para_entidad(
            nombre_entidad, TipoTrabajoOrquestador.CONSULTA_ENTIDAD, politica or self._politica_defecto, pasos,
        )

    def actualizar_entidad(self, nombre_entidad: str) -> ResultadoOrquestacionDTO:
        """Fuerza la Politica "Actualizacion Completa" -- revisa
        Transparencia/SENESCYT/Foro aunque exista cache vigente."""
        return self._ejecutar_para_entidad(
            nombre_entidad, TipoTrabajoOrquestador.ACTUALIZACION_ENTIDAD, "actualizacion_completa", None,
        )

    def consultar_masivo(self, politica: str | None = None) -> list[ResultadoOrquestacionDTO]:
        entidades = self._entidad_repository.listar_activas()
        return self._ejecutar_lote(
            [e.nombre for e in entidades], TipoTrabajoOrquestador.CONSULTA_MASIVA, politica or self._politica_defecto,
        )

    def actualizar_masivo(self) -> list[ResultadoOrquestacionDTO]:
        """Fuerza la Politica "Masiva Nocturna" (concurrencia limitada,
        prioriza pendientes, reintenta errores transitorios)."""
        entidades = self._entidad_repository.listar_activas()
        return self._ejecutar_lote(
            [e.nombre for e in entidades], TipoTrabajoOrquestador.ACTUALIZACION_MASIVA, "masiva_nocturna",
        )

    def consultar_por_filtro(self, filtros: FiltrosConsultaDTO, politica: str | None = None) -> list[ResultadoOrquestacionDTO]:
        """Reutiliza `FuncionarioRepositoryPort.buscar_con_filtros`
        (Submodulo 4.7, Modulo 4 congelado) para acotar las Entidades
        candidatas antes de correr el pipeline completo solo sobre
        ellas."""
        funcionarios_candidatos = self._funcionario_repository.buscar_con_filtros(filtros)
        entidad_ids = sorted({f.entidad_id for f in funcionarios_candidatos})
        nombres = []
        for entidad_id in entidad_ids:
            entidad = self._entidad_repository.buscar_por_id(entidad_id)
            if entidad is not None:
                nombres.append(entidad.nombre)
        return self._ejecutar_lote(nombres, TipoTrabajoOrquestador.CONSULTA_FILTRO, politica or self._politica_defecto)

    def reprocesar_job(self, trabajo_id: Any) -> ResultadoOrquestacionDTO:
        """Submodulo 9.7 (Reanudacion): retoma un `TrabajoOrquestador`
        existente (tipicamente en ERROR o PAUSADO) exactamente con los
        mismos parametros y politica con los que se creo."""
        trabajo = self._cola.buscar_por_id(trabajo_id)
        if trabajo is None:
            raise EntidadNoEncontradaError(f"TrabajoOrquestador no encontrado: {trabajo_id}")
        nombre_entidad = trabajo.parametros.get("nombre_entidad")
        if not nombre_entidad:
            raise EntidadNoEncontradaError(f"TrabajoOrquestador {trabajo_id} no tiene 'nombre_entidad' en sus parametros")

        if trabajo.estado == EstadoTrabajoOrquestador.ERROR:
            self._cola.reintentar_si_corresponde(trabajo)
        elif trabajo.estado == EstadoTrabajoOrquestador.PAUSADO:
            self._cola.reanudar(trabajo)

        return self._ejecutar_con_trabajo_existente(trabajo, nombre_entidad, None)

    # -- Orquestacion individual ------------------------------------------

    def _ejecutar_para_entidad(
        self, nombre_entidad: str, tipo_trabajo: TipoTrabajoOrquestador, nombre_politica: str,
        pasos: frozenset[TipoPasoPipeline] | None,
    ) -> ResultadoOrquestacionDTO:
        entidad = self._entidad_repository.buscar_por_nombre(nombre_entidad)
        if entidad is None or entidad.id is None:
            raise EntidadNoEncontradaError(f"Entidad no encontrada: '{nombre_entidad}'")

        trabajo = self._cola.encolar(
            tipo_trabajo, {"nombre_entidad": nombre_entidad}, nombre_politica, entidad_id=entidad.id,
        )
        return self._ejecutar_con_trabajo_existente(trabajo, nombre_entidad, pasos)

    def _ejecutar_con_trabajo_existente(
        self, trabajo: TrabajoOrquestador, nombre_entidad: str, pasos: frozenset[TipoPasoPipeline] | None,
    ) -> ResultadoOrquestacionDTO:
        entidad = self._entidad_repository.buscar_por_nombre(nombre_entidad)
        if entidad is None or entidad.id is None:
            raise EntidadNoEncontradaError(f"Entidad no encontrada: '{nombre_entidad}'")

        politica = self._motor_politicas.resolver(trabajo.politica)
        self._cola.iniciar_directo(trabajo)

        inicio = self._ahora_provider()
        try:
            resultado = self._ejecutar_pipeline_aislado(trabajo, entidad, politica, pasos)
        except GovDataError as exc:
            self._cola.marcar_error(trabajo, str(exc))
            raise

        fin = self._ahora_provider()
        if resultado["errores"]:
            self._cola.marcar_error(trabajo, "; ".join(resultado["errores"]))
        else:
            self._cola.marcar_completado(trabajo)

        return ResultadoOrquestacionDTO(
            job=asdict(TrabajoOrquestadorDTO.desde_entidad(trabajo)),
            entidad={"id": entidad.id, "nombre": entidad.nombre},
            estadisticas=asdict(resultado["estadisticas"]),
            funcionarios=resultado["funcionarios"],
            alertas=resultado["alertas"],
            errores=resultado["errores"],
            duracion_total=f"{(fin - inicio).total_seconds():.4f}s",
        )

    def _ejecutar_pipeline_aislado(
        self, trabajo: TrabajoOrquestador, entidad: Entidad, politica: PoliticaEjecucion,
        pasos_solicitados: frozenset[TipoPasoPipeline] | None,
    ) -> dict[str, Any]:
        """Ejecuta `_ejecutar_pipeline` en un hilo dedicado, creado y
        descartado en esta misma llamada (FASE 3.8 -- causa raiz
        confirmada con reproduccion real, no una suposicion).

        `MonitoreoContinuoService` (Modulo 5, paso Descubrimiento) usa la
        Sync API de Playwright, que EXIGE que el navegador se use siempre
        desde el mismo hilo del sistema operativo que lo creo -- nunca
        desde otro. FastAPI/Starlette ejecutan los endpoints sincronos (y
        sus `Depends`) via `anyio.to_thread.run_sync`, que REUTILIZA un
        pool de hilos worker entre peticiones distintas: no hay garantia
        de que cada peticion HTTP se sirva en un hilo nuevo. Cuando el
        hilo reciclado por ese pool para una peticion posterior coincide
        con uno que ya lanzo Playwright en una peticion anterior, la Sync
        API revienta con 'Sync API inside the asyncio loop' -- reproducido
        de forma controlada y secuencial (nunca concurrente) contra el
        portal real: primera consulta 200 OK, segunda consulta (mismo
        proceso, ~7s despues) 500 en <1s, antes de tocar la red.

        Un `ThreadPoolExecutor(max_workers=1)` creado aqui mismo, usado
        una sola vez y cerrado al salir del `with`, nunca se comparte con
        el pool de `anyio` ni se reutiliza entre peticiones -- cada
        consulta obtiene un hilo verdaderamente propio. `cerrar()` se
        ejecuta DENTRO de ese mismo hilo dedicado (nunca desde el hilo
        que llamo a este metodo), porque cerrar un navegador Playwright
        tambien debe hacerse desde el hilo que lo abrio; de paso corrige
        una fuga real confirmada: ningun llamador de
        `MonitoreoContinuoService.monitorear()` en el camino de la API
        cerraba el navegador -- quedaba huerfano indefinidamente."""

        def _tarea() -> dict[str, Any]:
            try:
                return self._ejecutar_pipeline(trabajo, entidad, politica, pasos_solicitados)
            finally:
                self._monitoreo_service.cerrar()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(_tarea).result()

    def _ejecutar_pipeline(
        self, trabajo: TrabajoOrquestador, entidad: Entidad, politica: PoliticaEjecucion,
        pasos_solicitados: frozenset[TipoPasoPipeline] | None,
    ) -> dict[str, Any]:
        if entidad.id is None:  # pragma: no cover -- garantizado por el llamador (_ejecutar_con_trabajo_existente)
            raise EntidadNoEncontradaError(f"Entidad '{entidad.nombre}' sin id -- inesperado tras persistirla")
        trabajo_id = str(trabajo.id)
        incluye = (lambda tipo: tipo in pasos_solicitados) if pasos_solicitados else (lambda _tipo: True)
        ahora = self._ahora_provider()

        errores: list[str] = []
        alertas: list[dict[str, Any]] = []
        funcionarios_consolidados: list[FuncionarioConsolidadoDTO] = []
        consultas_senescyt = consultas_foro = 0
        cache_hit = cache_miss = 0
        cambios_detectados = 0

        # -- Pasos 1-3: Transparencia (delegado a Monitoreo Continuo, Modulo 5) --
        hubo_cambio_transparencia = True
        if incluye(TipoPasoPipeline.DESCUBRIMIENTO):
            inicio_paso = self._ahora_provider()
            try:
                resultado_monitoreo = self._monitoreo_service.monitorear(entidad)
                hubo_cambio_transparencia = resultado_monitoreo.hubo_cambio
                fin_paso = self._ahora_provider()
                self._auditoria.registrar_ejecutado(
                    trabajo_id, TipoPasoPipeline.DESCUBRIMIENTO, inicio_paso, fin_paso,
                )
                for paso, se_ejecuto in (
                    (TipoPasoPipeline.DESCARGA, hubo_cambio_transparencia),
                    (TipoPasoPipeline.EXTRACCION, hubo_cambio_transparencia),
                    (TipoPasoPipeline.COMPARACION, hubo_cambio_transparencia),
                ):
                    if se_ejecuto:
                        cambios_detectados += len(resultado_monitoreo.comparacion.cambios) if resultado_monitoreo.comparacion else 0
                        self._auditoria.registrar_ejecutado(trabajo_id, paso, inicio_paso, fin_paso)
                    else:
                        self._auditoria.registrar_omitido(
                            trabajo_id, paso, resultado_monitoreo.verificacion.motivo, fin_paso,
                        )
            except GovDataError as exc:
                fin_paso = self._ahora_provider()
                errores.append(f"transparencia: {exc}")
                self._auditoria.registrar_fallido(trabajo_id, TipoPasoPipeline.DESCUBRIMIENTO, str(exc), inicio_paso, fin_paso)
        else:
            for paso in (TipoPasoPipeline.DESCUBRIMIENTO, TipoPasoPipeline.DESCARGA, TipoPasoPipeline.EXTRACCION):
                self._auditoria.registrar_omitido(trabajo_id, paso, "pipeline_parcial_no_solicitado", ahora)

        # -- Politica "Solo Cambios": sin cambios y entidad ya conocida -> --
        # -- no continua a SENESCYT/Foro/Perfil. --------------------------
        if politica.solo_cambios and not hubo_cambio_transparencia:
            for paso in (TipoPasoPipeline.SENESCYT, TipoPasoPipeline.FORO, TipoPasoPipeline.PERFIL, TipoPasoPipeline.ALERTAS):
                self._auditoria.registrar_omitido(trabajo_id, paso, "politica_solo_cambios_sin_novedad", ahora)
            estadisticas = EstadisticasOrquestacionDTO(
                funcionarios_juridicos=0, cambios_detectados=cambios_detectados, errores=len(errores),
            )
            return {"errores": errores, "alertas": alertas, "funcionarios": [], "estadisticas": estadisticas}

        funcionarios_juridicos = [
            f for f in self._funcionario_repository.listar_por_entidad(entidad.id, solo_vigentes=True)
            if f.area_clasificada == AreaRelevante.JURIDICA
        ]

        enriq_academico = self._crear_enriquecimiento_academico(politica) if incluye(TipoPasoPipeline.SENESCYT) else None
        enriq_foro = self._crear_enriquecimiento_foro(politica) if incluye(TipoPasoPipeline.FORO) else None
        if not incluye(TipoPasoPipeline.SENESCYT):
            self._auditoria.registrar_omitido(trabajo_id, TipoPasoPipeline.SENESCYT, "pipeline_parcial_no_solicitado", ahora)
        if not incluye(TipoPasoPipeline.FORO):
            self._auditoria.registrar_omitido(trabajo_id, TipoPasoPipeline.FORO, "pipeline_parcial_no_solicitado", ahora)

        for funcionario in funcionarios_juridicos:
            try:
                resultado_funcionario = self._procesar_funcionario(
                    trabajo_id, entidad, funcionario, enriq_academico, enriq_foro, incluye,
                )
            except GovDataError as exc:
                errores.append(f"{funcionario.persona_id}: {exc}")
                logger.warning("orquestacion_funcionario_fallo", entidad=entidad.nombre, persona_id=funcionario.persona_id, error=str(exc))
                continue
            if resultado_funcionario is None:
                continue
            consolidado, consulto_senescyt, consulto_foro, alertas_funcionario, cambios_funcionario = resultado_funcionario
            funcionarios_consolidados.append(consolidado)
            if consulto_senescyt is True:
                consultas_senescyt += 1
                cache_miss += 1
            elif consulto_senescyt is False:
                cache_hit += 1
            if consulto_foro is True:
                consultas_foro += 1
                cache_miss += 1
            elif consulto_foro is False:
                cache_hit += 1
            alertas.extend(alertas_funcionario)
            cambios_detectados += cambios_funcionario

        if incluye(TipoPasoPipeline.PERFIL):
            self._auditoria.registrar_ejecutado(
                trabajo_id, TipoPasoPipeline.PERFIL, ahora, self._ahora_provider(),
                cantidad_registros=len(funcionarios_juridicos),
            )
        else:
            self._auditoria.registrar_omitido(trabajo_id, TipoPasoPipeline.PERFIL, "pipeline_parcial_no_solicitado", ahora)

        if incluye(TipoPasoPipeline.ALERTAS):
            self._auditoria.registrar_ejecutado(
                trabajo_id, TipoPasoPipeline.ALERTAS, ahora, self._ahora_provider(), cantidad_registros=len(alertas),
            )
        else:
            self._auditoria.registrar_omitido(trabajo_id, TipoPasoPipeline.ALERTAS, "pipeline_parcial_no_solicitado", ahora)

        estadisticas = EstadisticasOrquestacionDTO(
            funcionarios_encontrados=len(self._funcionario_repository.listar_por_entidad(entidad.id, solo_vigentes=True)),
            funcionarios_juridicos=len(funcionarios_juridicos), consultas_senescyt=consultas_senescyt,
            consultas_foro=consultas_foro, cambios_detectados=cambios_detectados, alertas=len(alertas),
            errores=len(errores), cache_hit=cache_hit, cache_miss=cache_miss,
        )
        return {
            "errores": errores, "alertas": alertas,
            "funcionarios": [asdict(f) for f in funcionarios_consolidados], "estadisticas": estadisticas,
        }

    def _procesar_funcionario(
        self, trabajo_id: str, entidad: Entidad, funcionario: Funcionario,
        enriq_academico: EnriquecimientoAcademicoService | None, enriq_foro: EnriquecimientoForoService | None,
        incluye: Callable[[TipoPasoPipeline], bool],
    ) -> tuple[FuncionarioConsolidadoDTO, bool | None, bool | None, list[dict[str, Any]], int] | None:
        persona = self._persona_repository.buscar_por_id(funcionario.persona_id)
        if persona is None:
            return None

        cargo_texto = str(funcionario.cargo)
        persona_master = self._resolver_persona_master_use_case.ejecutar(persona, cargo=cargo_texto, institucion=entidad.nombre)
        if persona_master.id is None:  # pragma: no cover -- garantizado por el resolver
            return None

        consulto_senescyt: bool | None = None
        consulto_foro: bool | None = None
        cambios = 0

        if enriq_academico is not None:
            inicio_paso = self._ahora_provider()
            senales = senales_desde_persona_master(persona_master, cargo=cargo_texto, institucion=entidad.nombre)
            resultado_ac = enriq_academico.enriquecer(persona_master, senales)
            fin_paso = self._ahora_provider()
            consulto_senescyt = resultado_ac.consultado
            cambios += resultado_ac.cambios_detectados
            if resultado_ac.consultado:
                self._auditoria.registrar_ejecutado(
                    trabajo_id, TipoPasoPipeline.SENESCYT, inicio_paso, fin_paso,
                    cantidad_registros=resultado_ac.cambios_detectados,
                )
            else:
                self._auditoria.registrar_omitido(trabajo_id, TipoPasoPipeline.SENESCYT, "cache_vigente", fin_paso)

        if enriq_foro is not None:
            inicio_paso = self._ahora_provider()
            resultado_foro = enriq_foro.enriquecer(persona_master, persona)
            fin_paso = self._ahora_provider()
            consulto_foro = resultado_foro.consultado
            cambios += resultado_foro.cambios_detectados
            if resultado_foro.consultado:
                self._auditoria.registrar_ejecutado(
                    trabajo_id, TipoPasoPipeline.FORO, inicio_paso, fin_paso,
                    cantidad_registros=resultado_foro.cambios_detectados,
                )
            else:
                self._auditoria.registrar_omitido(trabajo_id, TipoPasoPipeline.FORO, "cache_vigente", fin_paso)

        # Paso 7 (Perfil): delega en `PerfilConsolidadoService` (Modulo 8,
        # REUTILIZADO) -- nunca se vuelve a leer `RegistroForo` a mano
        # aqui, se usa la misma fuente que el contrato 8.10.
        registro_foro_dict: dict[str, Any] | None = None
        if incluye(TipoPasoPipeline.PERFIL) and entidad.id is not None:
            perfil = self._perfil_consolidado_service.construir_perfil(persona_master.id, entidad.id)
            registros_foro = perfil.foro.get("registros", [])
            registro_foro_dict = registros_foro[0] if registros_foro else None

        fecha_consulta_foro = registro_foro_dict.get("fecha_consulta") if registro_foro_dict else None
        consolidado = FuncionarioConsolidadoDTO(
            nombre_completo=persona_master.nombre_completo.nombre_completo,
            cedula=persona.cedula,
            correo=str(persona_master.correo_principal) if persona_master.correo_principal else None,
            telefono=str(persona_master.telefono_principal) if persona_master.telefono_principal else None,
            extension_telefonica=persona.extension_telefonica,
            celular=registro_foro_dict.get("celular_personal") if registro_foro_dict else None,
            correo_personal=registro_foro_dict.get("correo_personal") if registro_foro_dict else None,
            cargo=cargo_texto,
            dependencia=funcionario.dependencia,
            registro_foro=registro_foro_dict.get("registro") if registro_foro_dict else None,
            estado_foro=registro_foro_dict.get("estado") if registro_foro_dict else None,
            provincia_foro=registro_foro_dict.get("provincia") if registro_foro_dict else None,
            fecha_consulta=fecha_consulta_foro.isoformat() if fecha_consulta_foro else None,
        )
        alertas_funcionario: list[dict[str, Any]] = []
        return consolidado, consulto_senescyt, consulto_foro, alertas_funcionario, cambios

    # -- Concurrencia real (Submodulos 9.5/9.6/9.8) -----------------------

    def _ejecutar_lote(
        self, nombres_entidad: list[str], tipo_trabajo: TipoTrabajoOrquestador, nombre_politica: str,
    ) -> list[ResultadoOrquestacionDTO]:
        politica = self._motor_politicas.resolver(nombre_politica)
        concurrencia = max(1, politica.concurrencia_maxima)

        if not nombres_entidad:
            return []

        if concurrencia == 1 or self._ejecutor_aislado is None:
            resultados: list[ResultadoOrquestacionDTO] = []
            for nombre in nombres_entidad:
                resultado = self._intentar_con_reintento(
                    self._crear_ejecucion_secuencial(nombre, tipo_trabajo, nombre_politica), nombre, politica,
                )
                if resultado is not None:
                    resultados.append(resultado)
            return resultados

        return self._ejecutar_lote_paralelo(nombres_entidad, tipo_trabajo, nombre_politica, politica, concurrencia)

    def _crear_ejecucion_secuencial(
        self, nombre_entidad: str, tipo_trabajo: TipoTrabajoOrquestador, nombre_politica: str,
    ) -> Callable[[], ResultadoOrquestacionDTO]:
        def _ejecutar() -> ResultadoOrquestacionDTO:
            return self._ejecutar_para_entidad(nombre_entidad, tipo_trabajo, nombre_politica, None)
        return _ejecutar

    @staticmethod
    def _crear_ejecucion_aislada(
        ejecutor_aislado: Callable[[str, TipoTrabajoOrquestador, str], ResultadoOrquestacionDTO],
        nombre_entidad: str, tipo_trabajo: TipoTrabajoOrquestador, nombre_politica: str,
    ) -> Callable[[], ResultadoOrquestacionDTO]:
        def _ejecutar() -> ResultadoOrquestacionDTO:
            return ejecutor_aislado(nombre_entidad, tipo_trabajo, nombre_politica)
        return _ejecutar

    def _intentar_con_reintento(
        self, ejecutar: Callable[[], ResultadoOrquestacionDTO], nombre_entidad: str, politica: PoliticaEjecucion,
    ) -> ResultadoOrquestacionDTO | None:
        """Submodulo 9.16 (Pruebas de reintentos): un fallo TRANSITORIO en
        una entidad, bajo una politica con `reintentos_automaticos=True`
        (ej. "Masiva Nocturna"), se reintenta UNA vez antes de darse por
        vencido -- sin bloquear al resto del lote."""
        try:
            return ejecutar()
        except GovDataError as exc:
            logger.warning("orquestacion_entidad_fallo", entidad=nombre_entidad, error=str(exc))
            if not politica.reintentos_automaticos:
                return None
            try:
                return ejecutar()
            except GovDataError as exc_reintento:
                logger.warning("orquestacion_entidad_reintento_fallo", entidad=nombre_entidad, error=str(exc_reintento))
                return None

    def _ejecutar_lote_paralelo(
        self, nombres_entidad: list[str], tipo_trabajo: TipoTrabajoOrquestador, nombre_politica: str,
        politica: PoliticaEjecucion, concurrencia: int,
    ) -> list[ResultadoOrquestacionDTO]:
        if self._ejecutor_aislado is None:  # pragma: no cover -- verificado por el llamador (_ejecutar_lote)
            raise OrquestacionFallidaError("ejecutor_aislado no configurado para ejecucion en paralelo")
        ejecutor_aislado = self._ejecutor_aislado

        cola_trabajo: queue.Queue[str | None] = queue.Queue()
        for nombre in nombres_entidad:
            cola_trabajo.put(nombre)
        cantidad_hilos = min(concurrencia, len(nombres_entidad))
        for _ in range(cantidad_hilos):
            cola_trabajo.put(_SENTINEL_FIN)

        resultados: list[ResultadoOrquestacionDTO] = []
        lock_resultados = threading.Lock()

        def _trabajador() -> None:
            while True:
                nombre = cola_trabajo.get()
                if nombre is _SENTINEL_FIN:
                    break
                # `ejecutor_aislado` abre y cierra SU PROPIA sesion por
                # llamada (inyectado por Container) -- cada item obtiene
                # su propia transaccion, nunca se comparte una `Session`
                # de SQLAlchemy entre hilos.
                resultado = self._intentar_con_reintento(
                    self._crear_ejecucion_aislada(ejecutor_aislado, nombre, tipo_trabajo, nombre_politica),
                    nombre, politica,
                )
                if resultado is not None:
                    with lock_resultados:
                        resultados.append(resultado)

        hilos = [threading.Thread(target=_trabajador) for _ in range(cantidad_hilos)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()
        return resultados
