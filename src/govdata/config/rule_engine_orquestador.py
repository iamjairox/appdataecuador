"""Motor de Reglas del Modulo 9: carga la configuracion externa (YAML) que
gobierna el Motor de Prioridades, el Motor de Politicas y la Cola de
Trabajos del Orquestador Maestro.

Archivo NUEVO, independiente de todos los `config/rule_engine*.py`
anteriores (Modulos 4/6/7/8, todos congelados) -- misma disciplina de
siempre: nada hardcodeado, el dominio nunca lee un YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError
from govdata.domain.rules.reglas_orquestador import (
    CatalogoPoliticas,
    PoliticaEjecucion,
    ReglasColaOrquestador,
    ReglasPrioridadEjecucion,
    RuleEngineOrquestador,
)

_RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
_DIR_REGLAS_DEFECTO = _RAIZ_PROYECTO / "config" / "rules"


def _leer_yaml(ruta: Path) -> dict:
    if not ruta.exists():
        raise ConfiguracionInvalidaError(f"Archivo de reglas no encontrado: {ruta}")
    try:
        with ruta.open(encoding="utf-8") as archivo:
            contenido = yaml.safe_load(archivo)
    except yaml.YAMLError as exc:
        raise ConfiguracionInvalidaError(f"YAML invalido en '{ruta}': {exc}") from exc
    if not isinstance(contenido, dict):
        raise ConfiguracionInvalidaError(f"'{ruta}' debe contener un mapeo YAML en la raiz")
    return contenido


def _cargar_prioridad(ruta: Path) -> ReglasPrioridadEjecucion:
    datos = _leer_yaml(ruta)
    return ReglasPrioridadEjecucion(
        peso_tiempo_sin_actualizacion=float(datos.get("peso_tiempo_sin_actualizacion", 1.0)),
        peso_cantidad_funcionarios=float(datos.get("peso_cantidad_funcionarios", 1.0)),
        peso_alertas_pendientes=float(datos.get("peso_alertas_pendientes", 2.0)),
        peso_cambios_recientes=float(datos.get("peso_cambios_recientes", 1.5)),
        peso_errores_anteriores=float(datos.get("peso_errores_anteriores", 1.0)),
        umbral_muy_alta=float(datos.get("umbral_muy_alta", 80.0)),
        umbral_alta=float(datos.get("umbral_alta", 50.0)),
        umbral_media=float(datos.get("umbral_media", 20.0)),
        horas_referencia_actualizacion=float(datos.get("horas_referencia_actualizacion", 24.0)),
        funcionarios_referencia=int(datos.get("funcionarios_referencia", 50)),
    )


def _cargar_politicas(ruta: Path) -> CatalogoPoliticas:
    datos = _leer_yaml(ruta)
    politicas_raw = datos.get("politicas")
    if not isinstance(politicas_raw, dict) or not politicas_raw:
        raise ConfiguracionInvalidaError(f"'{ruta}' requiere una clave 'politicas' no vacia")

    politicas: dict[str, PoliticaEjecucion] = {}
    for nombre, config in politicas_raw.items():
        if not isinstance(config, dict):
            raise ConfiguracionInvalidaError(f"La politica '{nombre}' en '{ruta}' debe ser un mapeo")
        politicas[nombre] = PoliticaEjecucion(
            nombre=nombre,
            usar_cache=bool(config.get("usar_cache", True)),
            forzar_actualizacion=bool(config.get("forzar_actualizacion", False)),
            solo_cambios=bool(config.get("solo_cambios", False)),
            concurrencia_maxima=int(config.get("concurrencia_maxima", 1)),
            reintentos_automaticos=bool(config.get("reintentos_automaticos", False)),
            prioridad_pendientes=bool(config.get("prioridad_pendientes", False)),
        )
    return CatalogoPoliticas(politicas_por_nombre=politicas)


def _cargar_cola(ruta: Path) -> ReglasColaOrquestador:
    datos = _leer_yaml(ruta)
    return ReglasColaOrquestador(
        concurrencia_maxima_defecto=int(datos.get("concurrencia_maxima_defecto", 2)),
        timeout_segundos_por_trabajo=float(datos.get("timeout_segundos_por_trabajo", 300.0)),
        max_reintentos_defecto=int(datos.get("max_reintentos_defecto", 3)),
        backoff_base_segundos=float(datos.get("backoff_base_segundos", 5.0)),
        politica_defecto=str(datos.get("politica_defecto", "consulta_rapida")),
    )


def cargar_rule_engine_orquestador(directorio_reglas: Path | str | None = None) -> RuleEngineOrquestador:
    directorio = Path(directorio_reglas) if directorio_reglas else _DIR_REGLAS_DEFECTO

    prioridad = _cargar_prioridad(directorio / "prioridades_orquestador.yaml")
    politicas = _cargar_politicas(directorio / "politicas_ejecucion.yaml")
    cola = _cargar_cola(directorio / "cola_orquestador.yaml")

    return RuleEngineOrquestador(prioridad=prioridad, politicas=politicas, cola=cola)
