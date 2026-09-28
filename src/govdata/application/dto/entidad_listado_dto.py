"""DTO: EntidadListadoDTO -- Modulo 10 (API REST), forma de UNA entidad en
`GET /entidades` y `GET /entidades/{id}`.

`tipo` se lee de `Entidad.metadata_extra["tipo_institucion"]` (Modulo 2,
`ListarEntidadesUseCase`, YA PERSISTIDO -- nunca se inventa). `provincia`/
`ciudad` quedan `None`: el portal DPE (Modulo 2) no captura esa
informacion todavia -- mismo limite ya documentado en `FiltrosConsultaDTO`
(Submodulo 4.7). `ultima_publicacion` viene de `PublicacionRepositoryPort.buscar_ultima_por_entidad`
(Modulo 2, congelado); `None` si la entidad nunca fue descubierta."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class EntidadListadoDTO:
    id: int
    nombre: str
    tipo: str | None
    provincia: str | None
    ciudad: str | None
    portal_origen: str
    estado: str
    ultima_publicacion: date | None
    ultima_actualizacion: datetime | None

    def to_dict(self) -> dict:
        return asdict(self)
