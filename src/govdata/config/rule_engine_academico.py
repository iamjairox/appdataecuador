"""Motor de Reglas del Modulo 7: carga la configuracion externa (YAML) que
gobierna el Normalizador Academico y el Cache por Persona.

Archivo NUEVO, independiente de `config/rule_engine.py` (Modulos 4/5) y
de `config/rule_engine_identidad.py` (Modulo 6, tambien congelado) --
misma disciplina de siempre: nada hardcodeado, el dominio nunca lee un
YAML.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError
from govdata.domain.rules.reglas_academicas import (
    CatalogoNormalizacion,
    ReglasCacheSenescyt,
    RuleEngineAcademico,
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


def _cargar_catalogo(ruta: Path) -> CatalogoNormalizacion:
    datos = _leer_yaml(ruta)
    canonicos = datos.get("canonicos")
    if not isinstance(canonicos, dict) or not canonicos:
        raise ConfiguracionInvalidaError(f"'{ruta}' requiere una clave 'canonicos' no vacia")
    return CatalogoNormalizacion(canonico_por_sinonimo={str(k): str(v) for k, v in canonicos.items()})


def cargar_rule_engine_academico(directorio_reglas: Path | str | None = None) -> RuleEngineAcademico:
    directorio = Path(directorio_reglas) if directorio_reglas else _DIR_REGLAS_DEFECTO

    titulos = _cargar_catalogo(directorio / "titulos.yaml")
    universidades = _cargar_catalogo(directorio / "universidades.yaml")
    niveles = _cargar_catalogo(directorio / "niveles.yaml")

    cache_raw = _leer_yaml(directorio / "cache_senescyt.yaml")
    cache = ReglasCacheSenescyt(dias_vigencia=int(cache_raw.get("dias_vigencia", 30)))

    return RuleEngineAcademico(titulos=titulos, universidades=universidades, niveles=niveles, cache=cache)
