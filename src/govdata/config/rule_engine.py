"""Motor de Reglas: carga la configuracion externa (YAML) que gobierna el
comportamiento del Modulo 4 -- sinonimos de columnas, diccionario de
clasificacion por area, y vigencia del cache.

Se agrego siguiendo una sugerencia explicita del cliente: en vez de
dispersar "que cargos son juridicos", "que sinonimos de columna existen"
o "cuantos dias dura el cache" por el codigo Python, todo eso vive en
`config/rules/*.yaml`. Adaptar el sistema a otra institucion, agregar un
area nueva, o ajustar un umbral es EDITAR UN ARCHIVO, nunca tocar logica.

Este modulo es el UNICO que sabe que la configuracion vive en archivos
YAML (frontera de infraestructura, por eso vive en `config/` y no en
`domain/`): lee los YAML y construye los tipos de dominio puros definidos
en `domain.rules.reglas_configurables` -- el dominio nunca importa este
modulo, es este modulo el que importa al dominio (Dependency Rule).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError
from govdata.domain.rules.reglas_configurables import (
    ReglasCache,
    ReglasClasificacion,
    ReglasCriticidad,
    ReglasNormalizacion,
    RuleEngine,
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


def cargar_rule_engine(directorio_reglas: Path | str | None = None) -> RuleEngine:
    """Carga los tres archivos de reglas y los valida minimamente.

    `directorio_reglas` es inyectable (tests pueden apuntar a un
    directorio temporal con reglas alternativas, sin tocar los YAML del
    proyecto).
    """
    directorio = Path(directorio_reglas) if directorio_reglas else _DIR_REGLAS_DEFECTO

    sinonimos_raw = _leer_yaml(directorio / "sinonimos_campos.yaml")
    campos = sinonimos_raw.get("campos")
    if not isinstance(campos, dict) or not campos:
        raise ConfiguracionInvalidaError("sinonimos_campos.yaml requiere una clave 'campos' no vacia")
    normalizacion = ReglasNormalizacion(sinonimos_por_campo=campos)

    clasificacion_raw = _leer_yaml(directorio / "clasificacion_areas.yaml")
    areas = clasificacion_raw.get("areas")
    if not isinstance(areas, dict) or not areas:
        raise ConfiguracionInvalidaError("clasificacion_areas.yaml requiere una clave 'areas' no vacia")
    cargos_por_area = {nombre_area: datos.get("cargos", []) for nombre_area, datos in areas.items()}
    palabras_clave_por_area = {nombre_area: datos.get("palabras_clave", []) for nombre_area, datos in areas.items()}
    niveles = clasificacion_raw.get("niveles_confianza", {})
    clasificacion = ReglasClasificacion(
        umbral_score_minimo=float(clasificacion_raw.get("umbral_score_minimo", 80.0)),
        nivel_alta=float(niveles.get("alta", 92.0)),
        nivel_media=float(niveles.get("media", 80.0)),
        cargos_por_area=cargos_por_area,
        palabras_clave_por_area=palabras_clave_por_area,
    )

    cache_raw = _leer_yaml(directorio / "vigencia_cache.yaml")
    cache = ReglasCache(dias_vigencia=int(cache_raw.get("dias_vigencia", 1)))

    criticidad = _cargar_reglas_criticidad(directorio / "criticidad_cambios.yaml")

    return RuleEngine(normalizacion=normalizacion, clasificacion=clasificacion, cache=cache, criticidad=criticidad)


def _cargar_reglas_criticidad(ruta: Path) -> ReglasCriticidad:
    """Modulo 5 (sugerencia del cliente): criticidad de un cambio segun el
    cargo involucrado (CRITICO/ALTO) o el campo modificado (MEDIO/BAJO).
    """
    datos = _leer_yaml(ruta)
    niveles = datos.get("niveles")
    if not isinstance(niveles, dict) or not niveles:
        raise ConfiguracionInvalidaError("criticidad_cambios.yaml requiere una clave 'niveles' no vacia")

    return ReglasCriticidad(
        umbral_score_minimo=float(datos.get("umbral_score_minimo", 80.0)),
        cargos_criticos=list(niveles.get("critico", {}).get("cargos", [])),
        cargos_altos=list(niveles.get("alto", {}).get("cargos", [])),
        campos_medios=list(niveles.get("medio", {}).get("campos", [])),
        umbral_cambio_masivo_pct=float(datos.get("umbral_cambio_masivo_pct", 30.0)),
        umbral_cambio_masivo_absoluto=int(datos.get("umbral_cambio_masivo_absoluto", 15)),
    )
