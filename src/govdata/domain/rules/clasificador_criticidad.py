"""Regla de dominio: Clasificador de Criticidad -- Modulo 5 (sugerencia
explicita del cliente: "no todos los cambios tienen el mismo valor para
el negocio").

Orden de decision para UNA `DiferenciaFuncionarioDTO`:

    1. ¿El CARGO coincide (fuzzy, mismo mecanismo que Submodulo 4.3) con
       el catalogo de cargos criticos? -> CRITICO.
    2. ¿Coincide con el catalogo de cargos altos? -> ALTO.
    3. ¿El campo modificado es correo/telefono (Submodulo, cualquier
       cargo)? -> MEDIO.
    4. ¿Es una correccion de nombre/apellido? -> BAJO (ejemplo explicito
       del cliente: "correcciones menores de formato o normalizacion").
    5. Cualquier otro cambio estructural (cargo/dependencia/area no
       especiales, funcionario nuevo/eliminado) -> MEDIO por defecto: es
       un cambio real de la relacion persona-entidad, mas relevante que
       una correccion de formato, pero no automaticamente critico/alto
       sin que el cargo lo amerite.

El paso 1-2 se evalua SIEMPRE primero, incluso para FUNCIONARIO_NUEVO/
FUNCIONARIO_ELIMINADO -- es exactamente lo que permite detectar "Nuevo
Director Juridico" como CRITICO (Submodulo 5.6).
"""

from __future__ import annotations

from dataclasses import replace

from rapidfuzz import fuzz

from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.domain.rules.normalizacion import normalizar_texto
from govdata.domain.rules.reglas_configurables import ReglasCriticidad
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_cambio import TipoCambio

_CAMPOS_NOMBRE = frozenset({"nombre", "apellido"})
_TIPOS_NOMBRE = frozenset({TipoCambio.CAMBIO_NOMBRE, TipoCambio.CAMBIO_APELLIDO})
_TIPOS_CONTACTO = frozenset({TipoCambio.CAMBIO_CORREO, TipoCambio.CAMBIO_TELEFONO})


def _mejor_score_contra_catalogo(cargo_normalizado: str, catalogo: list[str]) -> float:
    mejor = 0.0
    for candidato in catalogo:
        score = fuzz.token_sort_ratio(cargo_normalizado, normalizar_texto(candidato))
        mejor = max(mejor, score)
    return mejor


def clasificar_criticidad(diferencia: DiferenciaFuncionarioDTO, reglas: ReglasCriticidad) -> NivelCriticidad:
    """Determina el nivel de criticidad de negocio de una diferencia."""
    cargo_normalizado = normalizar_texto(diferencia.cargo)
    if cargo_normalizado:
        if _mejor_score_contra_catalogo(cargo_normalizado, reglas.cargos_criticos) >= reglas.umbral_score_minimo:
            return NivelCriticidad.CRITICO
        if _mejor_score_contra_catalogo(cargo_normalizado, reglas.cargos_altos) >= reglas.umbral_score_minimo:
            return NivelCriticidad.ALTO

    if diferencia.tipo_cambio in _TIPOS_CONTACTO:
        return NivelCriticidad.MEDIO
    if diferencia.tipo_cambio == TipoCambio.CAMBIO_MULTIPLE:
        campos_afectados = {campo.campo for campo in diferencia.campos_modificados}
        if campos_afectados & set(reglas.campos_medios):
            return NivelCriticidad.MEDIO
        if campos_afectados <= _CAMPOS_NOMBRE:
            return NivelCriticidad.BAJO
    if diferencia.tipo_cambio in _TIPOS_NOMBRE:
        return NivelCriticidad.BAJO
    if diferencia.tipo_cambio == TipoCambio.SIN_CAMBIOS:
        return NivelCriticidad.BAJO

    return NivelCriticidad.MEDIO


def enriquecer_con_criticidad(
    diferencias: list[DiferenciaFuncionarioDTO], reglas: ReglasCriticidad
) -> list[DiferenciaFuncionarioDTO]:
    """Devuelve una copia de `diferencias` con `criticidad` asignada a cada
    una -- el Motor de Comparacion (5.1) las produce con `criticidad=None`
    a proposito (separacion de responsabilidades: comparar no es lo mismo
    que juzgar el impacto de negocio)."""
    return [replace(d, criticidad=clasificar_criticidad(d, reglas)) for d in diferencias]
