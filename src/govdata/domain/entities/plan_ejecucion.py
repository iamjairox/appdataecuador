"""Entidad de dominio (en memoria, no persistida): PlanEjecucion --
Submodulo 9.3 (Planificador).

"Debe construir un plan de ejecucion... cada paso debe poder omitirse."
El plan es la INTENCION declarada antes de ejecutar (que pasos se van a
intentar, y cuales se omiten de entrada por una decision ESTATICA --
pipeline parcial 9.9, o una politica que no los necesita). La omision
DINAMICA (cache vigente, hash sin cambios -- que solo se conoce DURANTE
la ejecucion, porque la deciden los Modulos 5/7/8 ya congelados) se
registra aparte, en `AuditoriaEtapa`, a medida que cada paso se ejecuta
de verdad -- el plan nunca pretende adivinar una decision que no le
corresponde tomar."""

from __future__ import annotations

from dataclasses import dataclass, field

from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline

PASOS_EN_ORDEN: tuple[TipoPasoPipeline, ...] = (
    TipoPasoPipeline.DESCUBRIMIENTO,
    TipoPasoPipeline.DESCARGA,
    TipoPasoPipeline.EXTRACCION,
    TipoPasoPipeline.SENESCYT,
    TipoPasoPipeline.FORO,
    TipoPasoPipeline.COMPARACION,
    TipoPasoPipeline.PERFIL,
    TipoPasoPipeline.ALERTAS,
)


@dataclass(frozen=True, slots=True)
class PasoPlanEjecucion:
    tipo: TipoPasoPipeline
    se_omite: bool = False
    razon_omision: str | None = None


@dataclass(frozen=True, slots=True)
class PlanEjecucion:
    pasos: tuple[PasoPlanEjecucion, ...] = field(default_factory=tuple)

    def paso_incluido(self, tipo: TipoPasoPipeline) -> bool:
        paso = next((p for p in self.pasos if p.tipo == tipo), None)
        return paso is not None and not paso.se_omite

    @property
    def pasos_omitidos(self) -> tuple[PasoPlanEjecucion, ...]:
        return tuple(p for p in self.pasos if p.se_omite)

    @property
    def pasos_a_intentar(self) -> tuple[PasoPlanEjecucion, ...]:
        return tuple(p for p in self.pasos if not p.se_omite)
