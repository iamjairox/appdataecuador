"""DTO: FiltrosConsultaDTO -- Submodulo 4.7.

Extensible por diseno: agregar un filtro nuevo es agregar un campo
`None`-por-defecto aqui y su condicion correspondiente en
`FuncionarioRepositoryPort`/su implementacion SQL -- nunca reescribir
`ConsultaService`.

`provincia`/`ciudad` quedan definidos en el contrato pero AUN NO tienen
dato real que filtrar (el Modulo 2 no captura esa informacion del portal
DPE todavia) -- ver "mejoras futuras" en el informe del modulo.
"""

from __future__ import annotations

from dataclasses import dataclass

from govdata.domain.value_objects.area_relevante import AreaRelevante


@dataclass(frozen=True, slots=True)
class FiltrosConsultaDTO:
    provincia: str | None = None
    ciudad: str | None = None
    tipo_institucion: str | None = None
    area: AreaRelevante | None = None
    cargo_contiene: str | None = None
    correo_disponible: bool | None = None
    telefono_disponible: bool | None = None
