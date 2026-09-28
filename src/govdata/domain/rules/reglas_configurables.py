"""Estructuras de datos del Motor de Reglas -- puramente contenedores de
configuracion (sin ningun comportamiento de IO). Viven en `domain` porque
son lo que las reglas de dominio (`normalizador_universal.py`,
`clasificador_funcionarios.py`) reciben como parametro; QUIEN las carga
desde YAML (`config/rule_engine.py`, infraestructura) es un detalle que
al dominio no le importa -- el dominio nunca lee un archivo.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReglasNormalizacion:
    """Sinonimos de encabezado -> campo canonico (Submodulo 4.2)."""

    sinonimos_por_campo: dict[str, list[str]] = field(default_factory=dict)

    @property
    def campos_canonicos(self) -> tuple[str, ...]:
        return tuple(self.sinonimos_por_campo.keys())


@dataclass(frozen=True, slots=True)
class ReglasClasificacion:
    """Diccionario de cargos por area + umbrales (Submodulo 4.3)."""

    umbral_score_minimo: float
    nivel_alta: float
    nivel_media: float
    cargos_por_area: dict[str, list[str]] = field(default_factory=dict)
    palabras_clave_por_area: dict[str, list[str]] = field(default_factory=dict)
    """Respaldo de `cargos_por_area`: cargos reales del sector publico
    suelen ser frases largas y estructuradas (ej. "Analista Juridico 1
    del SFPS") que el fuzzy match de `cargos_por_area` no alcanza a
    reconocer por la diferencia de longitud/cantidad de palabras vs un
    candidato corto como "Asesor Juridico" (reproducido con datos reales
    de la SEPS: 28/28 cargos con "Juridico" quedaban por debajo del
    umbral). Si el cargo contiene una de estas palabras como TOKEN
    completo (no substring), se clasifica al area sin pasar por el
    fuzzy match -- confirmado con el usuario, autorizado explicitamente."""


@dataclass(frozen=True, slots=True)
class ReglasCache:
    """Vigencia del cache inteligente (Submodulo 4.9)."""

    dias_vigencia: int


@dataclass(frozen=True, slots=True)
class ReglasCriticidad:
    """Clasificacion de criticidad de un cambio (Modulo 5, sugerencia del
    cliente): CRITICO/ALTO se determinan por el CARGO involucrado (fuzzy
    match, mismo mecanismo que `ReglasClasificacion`); MEDIO/BAJO se
    determinan por el CAMPO que cambio cuando el cargo no es de interes
    especial.

    Dos umbrales de "cambio masivo" independientes (Submodulo 5.6),
    porque un porcentaje alto y un volumen alto son señales distintas:
    una entidad chica puede llegar al 30% con solo 2 cambios (poco
    interesante en volumen absoluto), y una entidad enorme puede sumar
    decenas de cambios reales sin llegar al 30% del total. Cualquiera de
    los dos, por separado, dispara su propia alerta.
    """

    umbral_score_minimo: float
    cargos_criticos: list[str] = field(default_factory=list)
    cargos_altos: list[str] = field(default_factory=list)
    campos_medios: list[str] = field(default_factory=list)
    umbral_cambio_masivo_pct: float = 30.0
    """% de funcionarios afectados (nuevos+eliminados+cambios sobre el
    total) a partir del cual se genera Alerta CAMBIO_SUPERIOR_30_PORCIENTO."""
    umbral_cambio_masivo_absoluto: int = 15
    """Cantidad ABSOLUTA de funcionarios afectados a partir de la cual se
    genera Alerta CAMBIO_MASIVO, independiente del porcentaje."""


@dataclass(frozen=True, slots=True)
class RuleEngine:
    """Punto unico de acceso a toda la configuracion externa de Modulos 4 y 5."""

    normalizacion: ReglasNormalizacion
    clasificacion: ReglasClasificacion
    cache: ReglasCache
    criticidad: ReglasCriticidad
