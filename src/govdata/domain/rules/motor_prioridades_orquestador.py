"""Regla de dominio: Motor de Prioridades del Orquestador -- Submodulo 9.5.

"Si existen 3.000 entidades: debe decidir cuales ejecutar primero."
Score compuesto 0-100, basado EXACTAMENTE en las 5 senales pedidas:
tiempo sin actualizacion, cantidad de funcionarios, alertas pendientes,
cambios recientes, errores anteriores -- cada una normalizada a [0, 1]
antes de ponderarse (asi ningun peso individual, por grande que sea,
puede dominar el score el solo mas alla de su proporcion configurada).

`alertas_pendientes`/`cambios_recientes`/`errores_anteriores` saturan en
1 (una sola alerta pendiente ya amerita el 100% de ese peso -- mas
alertas no empujan mas la prioridad, la SEÑAL es "hay algo pendiente",
no "cuanto"); `tiempo_sin_actualizacion_horas`/`cantidad_funcionarios`
escalan linealmente hasta su valor de referencia configurable."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from govdata.domain.rules.reglas_orquestador import ReglasPrioridadEjecucion
from govdata.domain.value_objects.nivel_prioridad_ejecucion import NivelPrioridadEjecucion


@dataclass(frozen=True, slots=True)
class SenalesPrioridad:
    tiempo_sin_actualizacion_horas: float = 0.0
    cantidad_funcionarios: int = 0
    alertas_pendientes: int = 0
    cambios_recientes: int = 0
    errores_anteriores: int = 0


def _normalizado(valor: float, referencia: float) -> float:
    if referencia <= 0:
        return 0.0
    return min(valor / referencia, 1.0)


def _saturado(valor: int) -> float:
    return 1.0 if valor > 0 else 0.0


def calcular_score(senales: SenalesPrioridad, reglas: ReglasPrioridadEjecucion) -> float:
    contribuciones = (
        (reglas.peso_tiempo_sin_actualizacion, _normalizado(senales.tiempo_sin_actualizacion_horas, reglas.horas_referencia_actualizacion)),
        (reglas.peso_cantidad_funcionarios, _normalizado(senales.cantidad_funcionarios, reglas.funcionarios_referencia)),
        (reglas.peso_alertas_pendientes, _saturado(senales.alertas_pendientes)),
        (reglas.peso_cambios_recientes, _saturado(senales.cambios_recientes)),
        (reglas.peso_errores_anteriores, _saturado(senales.errores_anteriores)),
    )
    peso_total = sum(peso for peso, _ in contribuciones)
    if peso_total <= 0:
        return 0.0
    return round(100.0 * sum(peso * valor for peso, valor in contribuciones) / peso_total, 4)


def calcular_prioridad(senales: SenalesPrioridad, reglas: ReglasPrioridadEjecucion) -> NivelPrioridadEjecucion:
    score = calcular_score(senales, reglas)
    if score >= reglas.umbral_muy_alta:
        return NivelPrioridadEjecucion.MUY_ALTA
    if score >= reglas.umbral_alta:
        return NivelPrioridadEjecucion.ALTA
    if score >= reglas.umbral_media:
        return NivelPrioridadEjecucion.MEDIA
    return NivelPrioridadEjecucion.BAJA


def ordenar_por_prioridad[T](
    candidatos: list[T], obtener_senales: Callable[[T], SenalesPrioridad], reglas: ReglasPrioridadEjecucion
) -> list[T]:
    """Ordena `candidatos` de mayor a menor score (estable)."""
    return sorted(candidatos, key=lambda c: calcular_score(obtener_senales(c), reglas), reverse=True)
