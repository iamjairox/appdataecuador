"""Motor de Reglas del Modulo 8: carga la configuracion externa (YAML) que
gobierna el Normalizador del Foro, el Cache por Persona y el Circuit
Breaker.

Archivo NUEVO, independiente de `config/rule_engine.py` (Modulos 4/5),
`config/rule_engine_identidad.py` (Modulo 6) y `config/rule_engine_academico.py`
(Modulo 7, todos congelados) -- misma disciplina de siempre: nada
hardcodeado, el dominio nunca lee un YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError
from govdata.domain.rules.reglas_foro import (
    CatalogoCamposForo,
    ReglasCacheForo,
    ReglasCircuitoForo,
    RuleEngineForo,
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


def _cargar_catalogo_campos(ruta: Path) -> CatalogoCamposForo:
    datos = _leer_yaml(ruta)
    campos = datos.get("campos")
    if not isinstance(campos, dict) or not campos:
        raise ConfiguracionInvalidaError(f"'{ruta}' requiere una clave 'campos' no vacia")
    return CatalogoCamposForo(campo_por_etiqueta={str(k): str(v) for k, v in campos.items()})


def cargar_rule_engine_foro(directorio_reglas: Path | str | None = None) -> RuleEngineForo:
    directorio = Path(directorio_reglas) if directorio_reglas else _DIR_REGLAS_DEFECTO

    campos = _cargar_catalogo_campos(directorio / "campos_foro.yaml")

    cache_raw = _leer_yaml(directorio / "cache_foro.yaml")
    cache = ReglasCacheForo(dias_vigencia=int(cache_raw.get("dias_vigencia", 7)))

    circuito_raw = _leer_yaml(directorio / "circuito_foro.yaml")
    circuito = ReglasCircuitoForo(
        umbral_fallos=int(circuito_raw.get("umbral_fallos", 5)),
        segundos_enfriamiento=float(circuito_raw.get("segundos_enfriamiento", 60.0)),
    )

    return RuleEngineForo(campos=campos, cache=cache, circuito=circuito)
