"""DTO: CambioEntidadDTO -- Modulo 10 (API REST), `GET /entidades/{id}/cambios`.

Fuente: `VersionFuncionario` (Modulo 5, `HistorialService.historial_de_dependencias`,
REUTILIZADO -- "nunca sobrescribir, toda modificacion abre una nueva
version"). `tipo_cambio`/`criticidad` se aceptan como filtro en la
especificacion pero NO estan persistidos en `VersionFuncionario` (esa
clasificacion, `DiferenciaFuncionarioDTO.tipo_cambio`/`criticidad`, es
TRANSIENTE -- se calcula durante la comparacion y se traduce de inmediato
en `Alerta`/`Evento`, nunca se guarda junto a la version); se documentan
como `None`, nunca inventados -- ver `GET /entidades/{id}/alertas` para
la version YA CLASIFICADA y persistida de este mismo feed."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class CambioEntidadDTO:
    persona_id: int
    numero_version: int
    cargo: str
    dependencia: str
    fecha_inicio: date
    fecha_fin: date | None
    tipo_cambio: str | None
    criticidad: str | None

    def to_dict(self) -> dict:
        return asdict(self)
