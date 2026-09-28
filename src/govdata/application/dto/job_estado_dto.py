"""DTO: JobEstadoDTO -- Modulo 10 (API REST), `GET /jobs/{job_id}`.

Junta lo que YA EXISTE en el Modulo 9 (congelado): `TrabajoOrquestadorDTO`
(estado/porcentaje-implicito-en-estado/duracion/errores/entidad/fechas) +
la lista de `AuditoriaEtapaDTO` (la "etapa" que pide la especificacion,
una fila por paso del Planificador -- Submodulo 9.3)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from govdata.application.dto.auditoria_etapa_dto import AuditoriaEtapaDTO
from govdata.application.dto.trabajo_orquestador_dto import TrabajoOrquestadorDTO


@dataclass(frozen=True, slots=True)
class JobEstadoDTO:
    trabajo: TrabajoOrquestadorDTO
    etapas: list[AuditoriaEtapaDTO] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
