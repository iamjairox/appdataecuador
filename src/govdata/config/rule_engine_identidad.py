"""Motor de Reglas del Modulo 6: carga la configuracion externa (YAML) que
gobierna el Motor de Identidad -- pesos de scoring, umbrales de fusion,
cache por fuente, priorizacion por cargo.

Deliberadamente un archivo NUEVO y SEPARADO de `config/rule_engine.py`
(Modulos 4/5, congelado): agregar aqui una linea a ese archivo violaria
la instruccion explicita de no modificar nada de los modulos aprobados.
Mismo patron, misma disciplina (el dominio nunca lee un YAML; este modulo
es la unica frontera que lo hace).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError
from govdata.domain.rules.reglas_identidad import (
    PesosScoring,
    ReglasCachePorFuente,
    ReglasPriorizacion,
    RuleEngineIdentidad,
    UmbralesFusion,
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


def cargar_rule_engine_identidad(directorio_reglas: Path | str | None = None) -> RuleEngineIdentidad:
    directorio = Path(directorio_reglas) if directorio_reglas else _DIR_REGLAS_DEFECTO

    scoring_raw = _leer_yaml(directorio / "scoring_identidad.yaml")
    pesos_raw = scoring_raw.get("pesos")
    if not isinstance(pesos_raw, dict) or not pesos_raw:
        raise ConfiguracionInvalidaError("scoring_identidad.yaml requiere una clave 'pesos' no vacia")
    scoring = PesosScoring(
        fingerprint=float(pesos_raw.get("fingerprint", 0.0)),
        correo=float(pesos_raw.get("correo", 0.0)),
        nombre=float(pesos_raw.get("nombre", 0.0)),
        apellido=float(pesos_raw.get("apellido", 0.0)),
        institucion=float(pesos_raw.get("institucion", 0.0)),
        cargo=float(pesos_raw.get("cargo", 0.0)),
        umbral_minimo_coincidencia=float(scoring_raw.get("umbral_minimo_coincidencia", 60.0)),
    )

    fusion_raw = _leer_yaml(directorio / "confianza_fusion.yaml")
    fusion = UmbralesFusion(
        umbral_fusion_automatica=float(fusion_raw.get("umbral_fusion_automatica", 98.0)),
        umbral_revision_manual=float(fusion_raw.get("umbral_revision_manual", 85.0)),
    )

    cache_raw = _leer_yaml(directorio / "cache_por_fuente.yaml")
    fuentes_raw = cache_raw.get("fuentes")
    if not isinstance(fuentes_raw, dict) or not fuentes_raw:
        raise ConfiguracionInvalidaError("cache_por_fuente.yaml requiere una clave 'fuentes' no vacia")
    cache_por_fuente = ReglasCachePorFuente(
        dias_por_fuente={str(k): int(v) for k, v in fuentes_raw.items()},
        dias_defecto=int(cache_raw.get("dias_defecto", 7)),
    )

    priorizacion_raw = _leer_yaml(directorio / "priorizacion_cargos.yaml")
    prioridades_raw = priorizacion_raw.get("prioridades")
    if not isinstance(prioridades_raw, dict) or not prioridades_raw:
        raise ConfiguracionInvalidaError("priorizacion_cargos.yaml requiere una clave 'prioridades' no vacia")
    priorizacion = ReglasPriorizacion(
        prioridad_por_cargo={str(k): float(v) for k, v in prioridades_raw.items()},
        prioridad_defecto=float(priorizacion_raw.get("prioridad_defecto", 10.0)),
        umbral_score_minimo=float(priorizacion_raw.get("umbral_score_minimo", 80.0)),
    )

    return RuleEngineIdentidad(
        scoring=scoring, fusion=fusion, cache_por_fuente=cache_por_fuente, priorizacion=priorizacion
    )
