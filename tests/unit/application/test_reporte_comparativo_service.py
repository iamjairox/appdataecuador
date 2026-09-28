"""Tests: reporte_comparativo_service (Submodulo 5.8) -- transformacion
pura de ResultadoComparacionDTO a ReporteComparativoDTO."""

from __future__ import annotations

from datetime import UTC, date, datetime

from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.application.dto.estadisticas_comparacion_dto import EstadisticasComparacionDTO
from govdata.application.dto.resultado_comparacion_dto import ResultadoComparacionDTO
from govdata.application.dto.resultado_unificado_dto import DocumentoResumenDTO, EntidadResumenDTO
from govdata.application.services.reporte_comparativo_service import generar_reporte
from govdata.domain.value_objects.tipo_cambio import TipoCambio


def _entidad() -> EntidadResumenDTO:
    return EntidadResumenDTO(id=1, nombre="Entidad X", portal_origen="dpe")


def _documento(mes: date, hash_="a" * 64) -> DocumentoResumenDTO:
    return DocumentoResumenDTO(id=1, tipo_archivo="pdf", mes_publicado=mes, hash_sha256=hash_, version=1, url="x")


def _diferencia(tipo: TipoCambio) -> DiferenciaFuncionarioDTO:
    return DiferenciaFuncionarioDTO(
        tipo_cambio=tipo, fingerprint="X", nombre="Juan", apellido="Perez", cargo="Director Juridico",
        dependencia="Legal", correo=None, telefono=None, area="juridica",
    )


class TestGenerarReporte:
    def test_primera_version_sin_documento_anterior(self) -> None:
        resultado = ResultadoComparacionDTO(
            entidad=_entidad(), documento_anterior=None, documento_actual=_documento(date(2026, 6, 1)),
            nuevos=[_diferencia(TipoCambio.FUNCIONARIO_NUEVO)], estadisticas=EstadisticasComparacionDTO(
                total_funcionarios_anteriores=0, total_funcionarios_actuales=1, cantidad_nuevos=1,
                cantidad_eliminados=0, cantidad_cambios=0, cantidad_sin_cambios=0, porcentaje_cambios=100.0,
            ),
            generado_en=datetime.now(UTC),
        )
        reporte = generar_reporte(resultado)
        assert reporte.periodo_anterior is None
        assert reporte.periodo_actual == "2026-06"
        assert "Primera version" in reporte.resumen_ejecutivo
        assert len(reporte.funcionarios_nuevos) == 1

    def test_comparacion_con_cambios_arma_resumen_ejecutivo(self) -> None:
        resultado = ResultadoComparacionDTO(
            entidad=_entidad(), documento_anterior=_documento(date(2026, 6, 1)), documento_actual=_documento(date(2026, 7, 1), "b" * 64),
            nuevos=[_diferencia(TipoCambio.FUNCIONARIO_NUEVO)],
            eliminados=[_diferencia(TipoCambio.FUNCIONARIO_ELIMINADO)],
            cambios=[_diferencia(TipoCambio.CAMBIO_CARGO)],
            sin_cambios=[_diferencia(TipoCambio.SIN_CAMBIOS), _diferencia(TipoCambio.SIN_CAMBIOS)],
            estadisticas=EstadisticasComparacionDTO(
                total_funcionarios_anteriores=4, total_funcionarios_actuales=4, cantidad_nuevos=1,
                cantidad_eliminados=1, cantidad_cambios=1, cantidad_sin_cambios=2, porcentaje_cambios=75.0,
            ),
            generado_en=datetime.now(UTC),
        )
        reporte = generar_reporte(resultado)
        assert reporte.periodo_anterior == "2026-06"
        assert reporte.periodo_actual == "2026-07"
        assert "1 funcionario(s) nuevo(s)" in reporte.resumen_ejecutivo
        assert "1 eliminado(s)" in reporte.resumen_ejecutivo
        assert "1 con cambios" in reporte.resumen_ejecutivo
        assert reporte.sin_cambios_cantidad == 2
        assert len(reporte.funcionarios_nuevos) == 1
        assert len(reporte.funcionarios_eliminados) == 1
        assert len(reporte.cambios) == 1

    def test_sin_diferencias_resumen_indica_sin_cambios(self) -> None:
        resultado = ResultadoComparacionDTO(
            entidad=_entidad(), documento_anterior=_documento(date(2026, 6, 1)), documento_actual=_documento(date(2026, 7, 1), "b" * 64),
            sin_cambios=[_diferencia(TipoCambio.SIN_CAMBIOS)],
            estadisticas=EstadisticasComparacionDTO(
                total_funcionarios_anteriores=1, total_funcionarios_actuales=1, cantidad_nuevos=0,
                cantidad_eliminados=0, cantidad_cambios=0, cantidad_sin_cambios=1, porcentaje_cambios=0.0,
            ),
            generado_en=datetime.now(UTC),
        )
        reporte = generar_reporte(resultado)
        assert "sin cambios" in reporte.resumen_ejecutivo

    def test_to_dict_es_serializable_como_json(self) -> None:
        import json

        resultado = ResultadoComparacionDTO(
            entidad=_entidad(), documento_anterior=None, documento_actual=_documento(date(2026, 6, 1)),
            estadisticas=EstadisticasComparacionDTO(
                total_funcionarios_anteriores=0, total_funcionarios_actuales=0, cantidad_nuevos=0,
                cantidad_eliminados=0, cantidad_cambios=0, cantidad_sin_cambios=0, porcentaje_cambios=0.0,
            ),
            generado_en=datetime.now(UTC),
        )
        reporte = generar_reporte(resultado)
        json.dumps(reporte.to_dict(), default=str)  # no debe lanzar
