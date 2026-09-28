"""DTO: EstadisticasComparacionDTO -- Submodulo 5.12.

Calculada por `domain.rules.motor_comparacion.calcular_estadisticas` a
partir de la lista de `DiferenciaFuncionarioDTO` de UNA comparacion --
nunca se recalcula por separado (evita que Estadisticas y Reporte
diverjan entre si)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class EstadisticasComparacionDTO:
    total_funcionarios_anteriores: int
    total_funcionarios_actuales: int
    cantidad_nuevos: int
    cantidad_eliminados: int
    cantidad_cambios: int
    """Funcionarios con al menos un campo modificado (incluye CAMBIO_MULTIPLE),
    SIN contar nuevos/eliminados."""
    cantidad_sin_cambios: int
    cambios_por_campo: dict[str, int] = field(default_factory=dict)
    """ej. {"cargo": 3, "dependencia": 1, "correo": 0, ...} -- cuenta
    ocurrencias de `CampoModificadoDTO.campo`, no funcionarios (un
    funcionario con CAMBIO_MULTIPLE aporta mas de una entrada)."""
    porcentaje_cambios: float = 0.0
    """(nuevos + eliminados + cambios) / max(total_anteriores, total_actuales) * 100."""
    duracion_segundos: float | None = None
