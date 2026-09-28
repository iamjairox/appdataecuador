"""Regla de dominio: Generador de Oportunidades Comerciales -- Submodulo
5.17 (preparacion para un futuro CRM).

"No implementar el CRM, solo generar eventos estructurados que luego
consumiran la API, el Dashboard o n8n" -- instruccion explicita del
cliente. Comparte el catalogo de cargos con `generador_alertas.py`
(mismo concepto -- "nuevo Director Juridico" es una Alerta operativa Y
una OportunidadComercial de negocio a la vez, con textos distintos para
audiencias distintas) pero es una lista deliberadamente MAS CORTA: solo
los patrones que el cliente listo explicitamente como "oportunidad", no
cualquier alerta operativa.
"""

from __future__ import annotations

from datetime import datetime

from rapidfuzz import fuzz

from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.application.dto.estadisticas_comparacion_dto import EstadisticasComparacionDTO
from govdata.domain.entities.oportunidad_comercial import OportunidadComercial, TipoOportunidad
from govdata.domain.rules.normalizacion import normalizar_texto
from govdata.domain.rules.reglas_configurables import ReglasCriticidad
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_cambio import TipoCambio

_UMBRAL_COINCIDENCIA_CARGO = 80.0

_CATALOGO_NUEVA_AUTORIDAD: tuple[tuple[tuple[str, ...], TipoOportunidad], ...] = (
    (("Director Juridico",), TipoOportunidad.NUEVO_DIRECTOR_JURIDICO),
    (("Procurador", "Procurador General"), TipoOportunidad.NUEVO_PROCURADOR),
    (("Director Financiero",), TipoOportunidad.NUEVO_DIRECTOR_FINANCIERO),
)
_CARGOS_MAXIMA_AUTORIDAD_JURIDICA: tuple[str, ...] = ("Director Juridico", "Procurador", "Procurador General")


def _coincide_con_alguno(cargo_normalizado: str, candidatos: tuple[str, ...]) -> bool:
    return any(
        fuzz.token_sort_ratio(cargo_normalizado, normalizar_texto(candidato)) >= _UMBRAL_COINCIDENCIA_CARGO
        for candidato in candidatos
    )


def generar_oportunidades_funcionario(
    diferencia: DiferenciaFuncionarioDTO, entidad_id: int, persona_id: int | None, detectado_en: datetime
) -> list[OportunidadComercial]:
    """Dos patrones distintos, ambos sobre el mismo campo `cargo`:

    - Contratacion EXTERNA directamente en un cargo de interes
      (`FUNCIONARIO_NUEVO`) -> `NUEVO_DIRECTOR_JURIDICO`/`NUEVO_PROCURADOR`/
      `NUEVO_DIRECTOR_FINANCIERO`.
    - Ascenso INTERNO hacia la maxima autoridad juridica (`CAMBIO_CARGO`
      o `CAMBIO_MULTIPLE` con `cargo` entre los campos modificados, cuyo
      valor NUEVO es Director Juridico/Procurador) -> distinta del caso
      anterior porque la persona YA era conocida por la plataforma.
    """
    cargo_normalizado = normalizar_texto(diferencia.cargo)
    if not cargo_normalizado:
        return []

    oportunidades: list[OportunidadComercial] = []

    if diferencia.tipo_cambio == TipoCambio.FUNCIONARIO_NUEVO:
        for candidatos, tipo in _CATALOGO_NUEVA_AUTORIDAD:
            if _coincide_con_alguno(cargo_normalizado, candidatos):
                oportunidades.append(
                    OportunidadComercial(
                        entidad_id=entidad_id,
                        tipo=tipo,
                        descripcion=f"{diferencia.nombre} {diferencia.apellido} ingreso como '{diferencia.cargo}'",
                        detectado_en=detectado_en,
                        persona_id=persona_id,
                        prioridad=NivelCriticidad.CRITICO,
                    )
                )

    if diferencia.tipo_cambio in (TipoCambio.CAMBIO_CARGO, TipoCambio.CAMBIO_MULTIPLE):
        cambio_cargo = next((c for c in diferencia.campos_modificados if c.campo == "cargo"), None)
        if cambio_cargo is not None and _coincide_con_alguno(cargo_normalizado, _CARGOS_MAXIMA_AUTORIDAD_JURIDICA):
            oportunidades.append(
                OportunidadComercial(
                    entidad_id=entidad_id,
                    tipo=TipoOportunidad.CAMBIO_MAXIMA_AUTORIDAD_JURIDICA,
                    descripcion=(
                        f"{diferencia.nombre} {diferencia.apellido} paso de "
                        f"'{cambio_cargo.valor_anterior}' a '{cambio_cargo.valor_nuevo}'"
                    ),
                    detectado_en=detectado_en,
                    persona_id=persona_id,
                    prioridad=NivelCriticidad.CRITICO,
                )
            )

    return oportunidades


def generar_oportunidades_documento(
    estadisticas: EstadisticasComparacionDTO, reglas: ReglasCriticidad, entidad_id: int, detectado_en: datetime
) -> list[OportunidadComercial]:
    """Cambio masivo de funcionarios -- señal de reestructuracion interna,
    interesante para el negocio independientemente de que cargos exactos
    cambiaron."""
    total_afectados = estadisticas.cantidad_nuevos + estadisticas.cantidad_eliminados + estadisticas.cantidad_cambios
    if (
        total_afectados < reglas.umbral_cambio_masivo_absoluto
        and estadisticas.porcentaje_cambios < reglas.umbral_cambio_masivo_pct
    ):
        return []

    return [
        OportunidadComercial(
            entidad_id=entidad_id,
            tipo=TipoOportunidad.CAMBIO_MASIVO_FUNCIONARIOS,
            descripcion=(
                f"Cambio masivo de funcionarios: {total_afectados} afectados "
                f"({estadisticas.porcentaje_cambios:.1f}% del total)"
            ),
            detectado_en=detectado_en,
            prioridad=NivelCriticidad.ALTO,
        )
    ]
