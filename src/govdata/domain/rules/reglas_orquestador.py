"""Estructuras de datos del Orquestador Maestro -- puros contenedores de
configuracion (sin IO), mismo patron que `reglas_foro.py` (Modulo 8).
Archivo NUEVO e independiente: Modulos 1-8 estan congelados.

Submodulo 9.13: "Todo configurable mediante YAML. Nunca hardcodeado." --
concurrencia, timeouts, reintentos, prioridades, cache y scheduler viven
todos aqui, cargados por `config/rule_engine_orquestador.py`."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReglasPrioridadEjecucion:
    """Pesos del Motor de Prioridades (Submodulo 9.5) -- cada senal aporta
    puntos a un score compuesto; los umbrales deciden el nivel final."""

    peso_tiempo_sin_actualizacion: float = 1.0
    peso_cantidad_funcionarios: float = 1.0
    peso_alertas_pendientes: float = 2.0
    peso_cambios_recientes: float = 1.5
    peso_errores_anteriores: float = 1.0
    umbral_muy_alta: float = 80.0
    umbral_alta: float = 50.0
    umbral_media: float = 20.0
    """Un score menor a `umbral_media` cae en BAJA."""
    horas_referencia_actualizacion: float = 24.0
    """Horas sin actualizar que aportan el 100% del
    `peso_tiempo_sin_actualizacion` (escala lineal, tope en 100%)."""
    funcionarios_referencia: int = 50
    """Cantidad de funcionarios juridicos que aporta el 100% del
    `peso_cantidad_funcionarios` (escala lineal, tope en 100%)."""


@dataclass(frozen=True, slots=True)
class PoliticaEjecucion:
    """Una politica de ejecucion configurable (mejora sugerida por el
    cliente al cierre del Modulo 8): en vez de reglas fijas en el
    Orquestador, el comportamiento completo de una corrida se resuelve
    seleccionando UNA politica por nombre."""

    nombre: str
    usar_cache: bool = True
    forzar_actualizacion: bool = False
    """Cuando es True, el Orquestador construye los servicios de
    Enriquecimiento (Modulos 7/8, REUTILIZADOS) con una vigencia de cache
    de 0 dias -- `debe_consultar()` siempre da True -- sin modificar ni
    una linea de esos servicios (ver `GovDataPipelineOrchestrator`)."""
    solo_cambios: bool = False
    """Solo continua a SENESCYT/Foro/Perfil si el Monitoreo Continuo
    (Modulo 5, REUTILIZADO) detecto `hubo_cambio=True` -- o si la entidad
    nunca fue procesada antes."""
    concurrencia_maxima: int = 1
    reintentos_automaticos: bool = False
    prioridad_pendientes: bool = False
    """Si es True, las entidades con alertas pendientes se ejecutan
    primero, sin importar el resto del Motor de Prioridades (9.5)."""


@dataclass(frozen=True, slots=True)
class CatalogoPoliticas:
    politicas_por_nombre: dict[str, PoliticaEjecucion] = field(default_factory=dict)

    def obtener(self, nombre: str) -> PoliticaEjecucion | None:
        return self.politicas_por_nombre.get(nombre)


@dataclass(frozen=True, slots=True)
class ReglasColaOrquestador:
    """Submodulos 9.6/9.7/9.8/9.13: comportamiento general de la cola."""

    concurrencia_maxima_defecto: int = 2
    timeout_segundos_por_trabajo: float = 300.0
    max_reintentos_defecto: int = 3
    backoff_base_segundos: float = 5.0
    politica_defecto: str = "consulta_rapida"


@dataclass(frozen=True, slots=True)
class RuleEngineOrquestador:
    """Punto unico de acceso a toda la configuracion externa del Modulo 9."""

    prioridad: ReglasPrioridadEjecucion
    politicas: CatalogoPoliticas
    cola: ReglasColaOrquestador
