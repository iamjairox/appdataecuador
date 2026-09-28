"""Regla de dominio: Planificador -- Submodulos 9.2 (Pipeline dinamico) y
9.3 (Planificador: "construir un plan de ejecucion... cada paso debe
poder omitirse").

Construye la parte ESTATICA del plan -- que pasos se van a INTENTAR,
declarada antes de ejecutar nada. Dos motivos legitimos para omitir un
paso de entrada, ambos resueltos aqui:

    1. Pipeline parcial (Submodulo 9.9): el llamador pidio explicitamente
       solo un subconjunto de pasos (ej. "solo Foro", mantenimiento).
    2. Politica: una `PoliticaEjecucion` (mejora del cliente) puede excluir
       pasos por diseno (ninguna de las 4 politicas base los excluye hoy,
       pero el mecanismo queda listo para politicas futuras).

La omision DINAMICA (cache vigente, documento sin cambios -- solo se sabe
DURANTE la ejecucion, la deciden Modulos 5/7/8 ya congelados) NO se
decide aqui -- ver `PlanEjecucion` y `AuditoriaEtapa`."""

from __future__ import annotations

from govdata.domain.entities.plan_ejecucion import PASOS_EN_ORDEN, PasoPlanEjecucion, PlanEjecucion
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline


def construir_plan(pasos_solicitados: frozenset[TipoPasoPipeline] | None = None) -> PlanEjecucion:
    """`pasos_solicitados=None` (o el conjunto completo) construye el
    pipeline COMPLETO -- ningun paso se omite de entrada. Un subconjunto
    (Submodulo 9.9) omite todo lo que no fue pedido, con razon explicita."""
    if pasos_solicitados is None:
        pasos = tuple(PasoPlanEjecucion(tipo=tipo) for tipo in PASOS_EN_ORDEN)
        return PlanEjecucion(pasos=pasos)

    pasos = tuple(
        PasoPlanEjecucion(tipo=tipo)
        if tipo in pasos_solicitados
        else PasoPlanEjecucion(tipo=tipo, se_omite=True, razon_omision="pipeline_parcial_no_solicitado")
        for tipo in PASOS_EN_ORDEN
    )
    return PlanEjecucion(pasos=pasos)
