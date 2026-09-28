"""DTOs: CampoModificadoDTO y DiferenciaFuncionarioDTO -- Submodulo 5.1
(Motor de Comparacion).

`CampoModificadoDTO` es la unidad ATOMICA de diferencia ("cada diferencia
debe quedar registrada"): un campo, su valor anterior, su valor nuevo.
`DiferenciaFuncionarioDTO` es la clasificacion AGREGADA de un funcionario
completo entre dos versiones de un documento (nuevo/eliminado/cambio de
un campo/cambio multiple/sin cambios), con la lista de `CampoModificadoDTO`
que la sustentan (vacia para NUEVO/ELIMINADO/SIN_CAMBIOS -- esos no son
diferencias campo a campo, son eventos de todo el registro).

Igual que `FuncionarioUnificadoDTO` (Modulo 4), esta forma NUNCA debe
cambiar de nombres de campo sin versionar el contrato: `ResultadoComparacionDTO`
(Submodulo 5.14) depende de ella.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_cambio import TipoCambio


@dataclass(frozen=True, slots=True)
class CampoModificadoDTO:
    """Una diferencia atomica: UN campo, su valor anterior y su valor nuevo."""

    campo: str
    valor_anterior: str | None
    valor_nuevo: str | None


@dataclass(frozen=True, slots=True)
class DiferenciaFuncionarioDTO:
    """Clasificacion agregada de UN funcionario entre dos versiones.

    Los campos `nombre`/`apellido`/`cargo`/.../`area` reflejan el estado
    ACTUAL (o, si `tipo_cambio == FUNCIONARIO_ELIMINADO`, el ultimo estado
    conocido -- ya no existe un "actual" para esa persona en esta entidad).
    """

    tipo_cambio: TipoCambio
    fingerprint: str
    nombre: str
    apellido: str
    cargo: str
    dependencia: str
    correo: str | None
    telefono: str | None
    area: str
    campos_modificados: tuple[CampoModificadoDTO, ...] = field(default_factory=tuple)
    criticidad: NivelCriticidad | None = None
    """Asignada en un segundo paso por `clasificador_criticidad` (Modulo 5,
    sugerencia del cliente) -- el Motor de Comparacion (5.1) no la calcula,
    solo produce la diferencia estructural."""

    @property
    def es_cambio(self) -> bool:
        """True para cualquier diferencia real (no aplica a SIN_CAMBIOS)."""
        return self.tipo_cambio != TipoCambio.SIN_CAMBIOS
