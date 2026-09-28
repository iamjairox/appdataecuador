"""Dobles de prueba de `GovDataPipelineOrchestrator` para los servicios
PESADOS de Modulos 5/6/7/8 (REUTILIZADOS, congelados) que el orquestador
solo invoca por su forma (duck-typing): `MonitoreoContinuoService`,
`ResolverOCrearPersonaMasterUseCase`, `PerfilConsolidadoService`,
`EnriquecimientoAcademicoService`, `EnriquecimientoForoService`.

Deliberadamente NO heredan de esas clases concretas -- sus grafos de
constructor (cache/consulta/comparacion/alerta/evento/rule_engine, etc.)
no aportan nada a estos tests; mypy nunca revisa `tests/`, asi que el
duck-typing es seguro aqui (mismo criterio usado para
`FakeMonitoreoContinuoService` en el resto del Modulo 9)."""

from __future__ import annotations

import threading
from typing import Any

from govdata.application.dto.resultado_enriquecimiento_academico_dto import (
    ResultadoEnriquecimientoAcademicoDTO,
)
from govdata.application.dto.resultado_enriquecimiento_foro_dto import (
    ResultadoEnriquecimientoForoDTO,
)
from govdata.application.dto.resultado_monitoreo_dto import ResultadoMonitoreoDTO
from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.application.dto.verificacion_dto import VerificacionDTO
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.persona import Persona
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.exceptions.domain_exceptions import GovDataError


def construir_resultado_monitoreo(
    entidad_id: int, hubo_cambio: bool, motivo: str, verificado_en: Any,
) -> ResultadoMonitoreoDTO:
    """Atajo para construir un `ResultadoMonitoreoDTO` valido en tests --
    `comparacion=None` siempre (el orquestador lo tolera incluso con
    `hubo_cambio=True`, ver `_ejecutar_pipeline`)."""
    return ResultadoMonitoreoDTO(
        entidad_id=entidad_id,
        hubo_cambio=hubo_cambio,
        verificacion=VerificacionDTO(
            entidad_id=entidad_id, hubo_cambio=hubo_cambio, motivo=motivo, verificado_en=verificado_en,
        ),
        comparacion=None,
    )


class FakeMonitoreoContinuoService:
    """Doble de `MonitoreoContinuoService` (Modulo 5, congelado)."""

    def __init__(
        self,
        resultado_por_entidad: dict[str, ResultadoMonitoreoDTO] | None = None,
        resultado_defecto: ResultadoMonitoreoDTO | None = None,
        entidades_con_error: dict[str, GovDataError] | None = None,
    ) -> None:
        self._resultado_por_entidad = resultado_por_entidad or {}
        self._resultado_defecto = resultado_defecto
        self._entidades_con_error = entidades_con_error or {}
        self.llamadas: list[str] = []
        self.veces_cerrado = 0
        self.hilos_de_llamada: list[int] = []
        """FASE 3.8: id del hilo del sistema operativo (`threading.get_ident()`)
        desde el que se invoco cada `monitorear()` -- permite verificar en
        tests que el pipeline corre en un hilo dedicado, nunca compartido
        entre dos consultas (causa raiz real del bug de Playwright)."""

    def monitorear(self, entidad: Entidad) -> ResultadoMonitoreoDTO:
        self.hilos_de_llamada.append(threading.get_ident())
        self.llamadas.append(entidad.nombre)
        if entidad.nombre in self._entidades_con_error:
            raise self._entidades_con_error[entidad.nombre]
        if entidad.nombre in self._resultado_por_entidad:
            return self._resultado_por_entidad[entidad.nombre]
        if self._resultado_defecto is not None:
            return self._resultado_defecto
        raise AssertionError(f"FakeMonitoreoContinuoService: sin resultado configurado para '{entidad.nombre}'")

    def cerrar(self) -> None:
        """FASE 3.8: el llamador real (`GovDataPipelineOrchestrator`)
        debe invocar esto tras cada `monitorear()`. Se cuenta para poder
        verificar en tests que efectivamente se invoca."""
        self.veces_cerrado += 1


class FakeResolverPersonaMasterUseCase:
    """Doble de `ResolverOCrearPersonaMasterUseCase` (Modulo 6, congelado)."""

    def __init__(
        self,
        persona_master_por_persona_id: dict[int, PersonaMaster] | None = None,
        personas_con_error: set[int] | None = None,
    ) -> None:
        self._mapa = persona_master_por_persona_id or {}
        self._personas_con_error = personas_con_error or set()
        self.llamadas: list[tuple[int, str | None, str | None]] = []

    def ejecutar(self, persona: Persona, cargo: str | None = None, institucion: str | None = None) -> PersonaMaster:
        assert persona.id is not None
        self.llamadas.append((persona.id, cargo, institucion))
        if persona.id in self._personas_con_error:
            raise GovDataError(f"identidad irresoluble para persona {persona.id}")
        if persona.id in self._mapa:
            return self._mapa[persona.id]
        return PersonaMaster(persona_id=persona.id, nombre_completo=persona.nombre_completo, id=persona.id)


class _PerfilConsolidadoFalso:
    def __init__(self, foro: dict[str, Any]) -> None:
        self.persona: dict[str, Any] = {}
        self.transparencia: dict[str, Any] = {}
        self.senescyt: dict[str, Any] = {}
        self.foro = foro


class FakePerfilConsolidadoService:
    """Doble de `PerfilConsolidadoService` (Modulo 8, congelado, Paso 7)."""

    def __init__(self, registros_foro_por_persona_master: dict[int, list[dict[str, Any]]] | None = None) -> None:
        self._mapa = registros_foro_por_persona_master or {}
        self.llamadas: list[tuple[int, int | None]] = []

    def construir_perfil(self, persona_master_id: int, entidad_id: int | None = None) -> _PerfilConsolidadoFalso:
        self.llamadas.append((persona_master_id, entidad_id))
        registros = self._mapa.get(persona_master_id, [])
        return _PerfilConsolidadoFalso(foro={"registros": registros})


class FakeEnriquecimientoAcademicoService:
    """Doble de `EnriquecimientoAcademicoService` (Modulo 7, congelado,
    Paso 4). `consultado=False` simula respuesta 100% desde cache
    (Submodulo 7.10) -- ver el "truco" del `dias_vigencia=0` en el
    docstring de `GovDataPipelineOrchestrator`."""

    def __init__(self, consultado: bool = True, cambios_detectados: int = 0) -> None:
        self.consultado = consultado
        self.cambios_detectados = cambios_detectados
        self.llamadas: list[int] = []

    def enriquecer(
        self, persona_master: PersonaMaster, senales: SenalesIdentidadDTO,
    ) -> ResultadoEnriquecimientoAcademicoDTO:
        assert persona_master.id is not None
        self.llamadas.append(persona_master.id)
        return ResultadoEnriquecimientoAcademicoDTO(
            persona_master_id=persona_master.id, consultado=self.consultado, cambios_detectados=self.cambios_detectados,
        )


class FakeEnriquecimientoForoService:
    """Doble de `EnriquecimientoForoService` (Modulo 8, congelado, Paso 5)."""

    def __init__(self, consultado: bool = True, cambios_detectados: int = 0) -> None:
        self.consultado = consultado
        self.cambios_detectados = cambios_detectados
        self.llamadas: list[int] = []

    def enriquecer(self, persona_master: PersonaMaster, persona: Persona) -> ResultadoEnriquecimientoForoDTO:
        assert persona_master.id is not None
        self.llamadas.append(persona_master.id)
        return ResultadoEnriquecimientoForoDTO(
            persona_master_id=persona_master.id, consultado=self.consultado, cambios_detectados=self.cambios_detectados,
        )
