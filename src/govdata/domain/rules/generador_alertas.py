"""Regla de dominio: Generador de Alertas -- Submodulo 5.6.

Convierte diferencias YA clasificadas por criticidad
(`clasificador_criticidad.enriquecer_con_criticidad`) en `Alerta`
persistibles. NO toda diferencia genera una alerta -- solo las que
coinciden con un patron de interes explicito del cliente:

    - Nuevo Director Juridico / Financiero / Procurador / Abogado
    - Funcionario eliminado
    - Cambio de correo / dependencia / cargo
    - Documento vacio / documento sospechoso (a nivel de todo el resultado,
      no de un funcionario -- ver `generar_alertas_documento`)
    - Cambio masivo / cambio superior al 30% (a nivel de todo el
      resultado, segun `EstadisticasComparacionDTO`)

Un `CAMBIO_MULTIPLE` que involucre correo Y cargo genera DOS alertas (una
por cada patron que calce) -- nunca se pierde una señal de negocio por
"ya se genero una alerta para este funcionario".
"""

from __future__ import annotations

from datetime import datetime

from rapidfuzz import fuzz

from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.application.dto.estadisticas_comparacion_dto import EstadisticasComparacionDTO
from govdata.domain.entities.alerta import Alerta, TipoAlerta
from govdata.domain.rules.normalizacion import normalizar_texto
from govdata.domain.rules.reglas_configurables import ReglasCriticidad
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_cambio import TipoCambio

_UMBRAL_COINCIDENCIA_CARGO = 80.0

_CATALOGO_NUEVO_CARGO: tuple[tuple[tuple[str, ...], TipoAlerta], ...] = (
    (("Director Juridico",), TipoAlerta.NUEVO_DIRECTOR_JURIDICO),
    (("Director Financiero",), TipoAlerta.NUEVO_DIRECTOR_FINANCIERO),
    (("Procurador", "Procurador General"), TipoAlerta.NUEVO_PROCURADOR),
    (("Abogado",), TipoAlerta.NUEVO_ABOGADO),
)

_TIPO_ALERTA_POR_CAMPO: dict[str, TipoAlerta] = {
    "correo": TipoAlerta.CAMBIO_CORREO,
    "dependencia": TipoAlerta.CAMBIO_DEPENDENCIA,
    "cargo": TipoAlerta.CAMBIO_CARGO,
}


def _coincide_con_alguno(cargo_normalizado: str, candidatos: tuple[str, ...]) -> bool:
    return any(
        fuzz.token_sort_ratio(cargo_normalizado, normalizar_texto(candidato)) >= _UMBRAL_COINCIDENCIA_CARGO
        for candidato in candidatos
    )


def generar_alertas_funcionario(
    diferencia: DiferenciaFuncionarioDTO,
    entidad_id: int,
    documento_id: int,
    persona_id: int | None,
    detectado_en: datetime,
) -> list[Alerta]:
    """Alertas derivadas de UN funcionario (nuevo/eliminado/campos cambiados)."""
    alertas: list[Alerta] = []
    criticidad = diferencia.criticidad or NivelCriticidad.MEDIO
    cargo_normalizado = normalizar_texto(diferencia.cargo)

    if diferencia.tipo_cambio == TipoCambio.FUNCIONARIO_NUEVO and cargo_normalizado:
        for candidatos, tipo_alerta in _CATALOGO_NUEVO_CARGO:
            if _coincide_con_alguno(cargo_normalizado, candidatos):
                alertas.append(
                    Alerta(
                        entidad_id=entidad_id,
                        tipo=tipo_alerta,
                        prioridad=criticidad,
                        descripcion=f"Nuevo funcionario en cargo '{diferencia.cargo}': {diferencia.nombre} {diferencia.apellido}",
                        detectado_en=detectado_en,
                        persona_id=persona_id,
                        documento_id=documento_id,
                    )
                )

    if diferencia.tipo_cambio == TipoCambio.FUNCIONARIO_ELIMINADO:
        alertas.append(
            Alerta(
                entidad_id=entidad_id,
                tipo=TipoAlerta.FUNCIONARIO_ELIMINADO,
                prioridad=criticidad,
                descripcion=f"Funcionario ya no aparece en el directorio: {diferencia.nombre} {diferencia.apellido} ({diferencia.cargo})",
                detectado_en=detectado_en,
                persona_id=persona_id,
                documento_id=documento_id,
            )
        )

    campos_modificados = {c.campo for c in diferencia.campos_modificados}
    for campo, tipo_alerta in _TIPO_ALERTA_POR_CAMPO.items():
        if campo in campos_modificados:
            alertas.append(
                Alerta(
                    entidad_id=entidad_id,
                    tipo=tipo_alerta,
                    prioridad=criticidad,
                    descripcion=f"Cambio de {campo} para {diferencia.nombre} {diferencia.apellido}: '{diferencia.cargo}'",
                    detectado_en=detectado_en,
                    persona_id=persona_id,
                    documento_id=documento_id,
                )
            )

    return alertas


def generar_alertas_documento(
    estadisticas: EstadisticasComparacionDTO,
    reglas: ReglasCriticidad,
    entidad_id: int,
    documento_id: int,
    detectado_en: datetime,
) -> list[Alerta]:
    """Alertas a nivel de TODO el resultado de comparacion: cambio masivo
    (absoluto), cambio superior al umbral (relativo), y documento vacio."""
    alertas: list[Alerta] = []
    total_afectados = estadisticas.cantidad_nuevos + estadisticas.cantidad_eliminados + estadisticas.cantidad_cambios

    if total_afectados >= reglas.umbral_cambio_masivo_absoluto:
        alertas.append(
            Alerta(
                entidad_id=entidad_id,
                tipo=TipoAlerta.CAMBIO_MASIVO,
                prioridad=NivelCriticidad.ALTO,
                descripcion=(
                    f"{total_afectados} funcionarios afectados en un solo documento "
                    f"(umbral: {reglas.umbral_cambio_masivo_absoluto})"
                ),
                detectado_en=detectado_en,
                documento_id=documento_id,
            )
        )

    if estadisticas.porcentaje_cambios >= reglas.umbral_cambio_masivo_pct:
        alertas.append(
            Alerta(
                entidad_id=entidad_id,
                tipo=TipoAlerta.CAMBIO_SUPERIOR_30_PORCIENTO,
                prioridad=NivelCriticidad.CRITICO,
                descripcion=(
                    f"{estadisticas.porcentaje_cambios:.1f}% de los funcionarios cambiaron "
                    f"(umbral: {reglas.umbral_cambio_masivo_pct:.0f}%)"
                ),
                detectado_en=detectado_en,
                documento_id=documento_id,
            )
        )

    if estadisticas.total_funcionarios_anteriores > 0 and estadisticas.total_funcionarios_actuales == 0:
        alertas.append(
            Alerta(
                entidad_id=entidad_id,
                tipo=TipoAlerta.DOCUMENTO_VACIO,
                prioridad=NivelCriticidad.ALTO,
                descripcion="El documento actual no produjo ningun funcionario (posible documento vacio o corrupto)",
                detectado_en=detectado_en,
                documento_id=documento_id,
            )
        )
    elif (
        estadisticas.total_funcionarios_anteriores >= 5
        and 0 < estadisticas.total_funcionarios_actuales < estadisticas.total_funcionarios_anteriores * 0.1
    ):
        # No llego a CERO (eso ya es DOCUMENTO_VACIO), pero perdio mas del
        # 90% de los funcionarios de golpe -- tipicamente sintoma de una
        # extraccion parcial (tabla mal detectada, encabezados corridos),
        # no de un recorte de personal real. Se marca para revision manual.
        alertas.append(
            Alerta(
                entidad_id=entidad_id,
                tipo=TipoAlerta.DOCUMENTO_SOSPECHOSO,
                prioridad=NivelCriticidad.ALTO,
                descripcion=(
                    f"Caida abrupta de {estadisticas.total_funcionarios_anteriores} a "
                    f"{estadisticas.total_funcionarios_actuales} funcionarios -- posible extraccion parcial"
                ),
                detectado_en=detectado_en,
                documento_id=documento_id,
            )
        )

    return alertas
