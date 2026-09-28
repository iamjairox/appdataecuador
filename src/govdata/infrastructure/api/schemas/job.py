"""Schemas Pydantic: Job -- Modulo 10, `GET /jobs/{job_id}`.

Sobre `TrabajoOrquestador` (Submodulo 9.6, la cola persistente real del
Modulo 9) + `AuditoriaEtapa` (9.10/9.15, una fila por paso ejecutado)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from govdata.application.dto.job_estado_dto import JobEstadoDTO


class EtapaJobSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tipo_paso: str
    estado_paso: str
    iniciado_en: datetime
    finalizado_en: datetime | None = None
    duracion_segundos: float | None = None
    razon_omision: str | None = None
    cantidad_registros: int
    error: str | None = None


class JobResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tipo: str
    estado: str
    prioridad: str
    politica: str
    parametros: dict[str, Any]
    intentos: int
    max_intentos: int
    entidad_id: int | None = None
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None
    iniciado_en: datetime | None = None
    finalizado_en: datetime | None = None
    ultimo_error: str | None = None
    etapas: list[EtapaJobSchema]

    @classmethod
    def desde_job_estado_dto(cls, job_estado: JobEstadoDTO) -> JobResponseSchema:
        trabajo = job_estado.trabajo
        return cls(
            id=trabajo.id, tipo=trabajo.tipo, estado=trabajo.estado, prioridad=trabajo.prioridad,
            politica=trabajo.politica, parametros=trabajo.parametros, intentos=trabajo.intentos,
            max_intentos=trabajo.max_intentos, entidad_id=trabajo.entidad_id, creado_en=trabajo.creado_en,
            actualizado_en=trabajo.actualizado_en, iniciado_en=trabajo.iniciado_en,
            finalizado_en=trabajo.finalizado_en, ultimo_error=trabajo.ultimo_error,
            etapas=[EtapaJobSchema.model_validate(e) for e in job_estado.etapas],
        )
