"""Value Object: NivelCriticidad.

Sugerido explicitamente por el cliente ("no todos los cambios tienen el
mismo valor para el negocio"): clasifica tanto `DiferenciaFuncionario`
como `Alerta`/`OportunidadComercial`, para que a futuro n8n pueda decidir
"notificar ya" vs "agrupar en un reporte diario/semanal" sin logica
adicional -- el nivel ya viaja con el dato.

Orden de severidad (de mayor a menor): CRITICO > ALTO > MEDIO > BAJO. Se
expone `IntEnum`-like orden via `_ORDEN` para poder comparar sin acoplar
al orden de declaracion del enum.
"""

from __future__ import annotations

from enum import Enum


class NivelCriticidad(str, Enum):
    CRITICO = "critico"
    ALTO = "alto"
    MEDIO = "medio"
    BAJO = "bajo"


_ORDEN: dict[NivelCriticidad, int] = {
    NivelCriticidad.BAJO: 0,
    NivelCriticidad.MEDIO: 1,
    NivelCriticidad.ALTO: 2,
    NivelCriticidad.CRITICO: 3,
}


def es_mas_critico(a: NivelCriticidad, b: NivelCriticidad) -> bool:
    """True si `a` es estrictamente mas severo que `b`."""
    return _ORDEN[a] > _ORDEN[b]


def mas_severo(niveles: list[NivelCriticidad]) -> NivelCriticidad:
    """El nivel mas severo de una lista no vacia -- usado para agregar la
    criticidad de un funcionario con `CAMBIO_MULTIPLE` (varias diferencias,
    cada una con su propio nivel)."""
    return max(niveles, key=lambda n: _ORDEN[n])
