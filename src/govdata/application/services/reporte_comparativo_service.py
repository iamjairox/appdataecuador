"""Servicio: ReporteComparativoService -- Submodulo 5.8.

Transforma un `ResultadoComparacionDTO` (5.14, ya calculado -- nunca se
recalcula nada aqui) en un `ReporteComparativoDTO` de LECTURA HUMANA, con
un resumen ejecutivo en texto plano. Sin dependencias de persistencia:
es una funcion de transformacion pura sobre DTOs ya construidos.
"""

from __future__ import annotations

from datetime import date

from govdata.application.dto.reporte_comparativo_dto import ReporteComparativoDTO
from govdata.application.dto.resultado_comparacion_dto import ResultadoComparacionDTO


def _periodo(fecha: date | None) -> str | None:
    return fecha.strftime("%Y-%m") if fecha is not None else None


def _resumen_ejecutivo(resultado: ResultadoComparacionDTO) -> str:
    stats = resultado.estadisticas
    if stats is None:
        return f"Comparacion de '{resultado.entidad.nombre}': sin estadisticas disponibles."

    if resultado.documento_anterior is None:
        return (
            f"Primera version conocida de '{resultado.entidad.nombre}': "
            f"{stats.total_funcionarios_actuales} funcionarios registrados."
        )

    partes = [f"Comparacion de '{resultado.entidad.nombre}':"]
    if stats.cantidad_nuevos:
        partes.append(f"{stats.cantidad_nuevos} funcionario(s) nuevo(s)")
    if stats.cantidad_eliminados:
        partes.append(f"{stats.cantidad_eliminados} eliminado(s)")
    if stats.cantidad_cambios:
        partes.append(f"{stats.cantidad_cambios} con cambios")
    if len(partes) == 1:
        return f"{partes[0]} sin cambios respecto al periodo anterior."

    resumen = ", ".join(partes[1:])
    return f"{partes[0]} {resumen} ({stats.porcentaje_cambios:.1f}% del total afectado)."


def generar_reporte(resultado: ResultadoComparacionDTO) -> ReporteComparativoDTO:
    stats = resultado.estadisticas
    return ReporteComparativoDTO(
        entidad=resultado.entidad,
        periodo_anterior=_periodo(resultado.documento_anterior.mes_publicado) if resultado.documento_anterior else None,
        periodo_actual=_periodo(resultado.documento_actual.mes_publicado) or "",
        resumen_ejecutivo=_resumen_ejecutivo(resultado),
        funcionarios_nuevos=resultado.nuevos,
        funcionarios_eliminados=resultado.eliminados,
        cambios=resultado.cambios,
        sin_cambios_cantidad=len(resultado.sin_cambios),
        estadisticas=stats,  # type: ignore[arg-type]
        alertas=resultado.alertas,
        generado_en=resultado.generado_en,
    )
