"""DTO: ReporteComparativoDTO -- Submodulo 5.8.

Vista de LECTURA HUMANA sobre un `ResultadoComparacionDTO` ya calculado
(nunca recalcula nada -- solo reempaqueta + agrega `resumen_ejecutivo`).
`sin_cambios_cantidad` es deliberadamente un conteo, no la lista completa:
un reporte para un humano (o un futuro PDF) no necesita listar cada
funcionario que no cambio, solo cuantos fueron.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

from govdata.application.dto.alerta_dto import AlertaDTO
from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.application.dto.estadisticas_comparacion_dto import EstadisticasComparacionDTO
from govdata.application.dto.resultado_unificado_dto import EntidadResumenDTO


@dataclass(frozen=True, slots=True)
class ReporteComparativoDTO:
    entidad: EntidadResumenDTO
    periodo_anterior: str | None
    """Mes publicado del documento anterior, formato 'YYYY-MM' (None si es
    la primera version conocida)."""
    periodo_actual: str
    resumen_ejecutivo: str
    funcionarios_nuevos: list[DiferenciaFuncionarioDTO]
    funcionarios_eliminados: list[DiferenciaFuncionarioDTO]
    cambios: list[DiferenciaFuncionarioDTO]
    sin_cambios_cantidad: int
    estadisticas: EstadisticasComparacionDTO
    alertas: list[AlertaDTO] = field(default_factory=list)
    generado_en: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        """Formato JSON -- tambien la base directa para un futuro
        renderizador PDF (Submodulo 5.8: "preparado para PDF futuro"):
        cada campo es texto/numero plano, sin objetos de dominio."""
        return asdict(self)
