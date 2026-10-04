"""Schemas Pydantic: Funcionario -- Modulo 10."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FuncionarioResponseSchema(BaseModel):
    """UNA fila de `GET /entidades/{id}/funcionarios` -- solo informacion
    YA PERSISTIDA (Modulos 1/4), nunca dispara SENESCYT/Foro."""

    model_config = ConfigDict(from_attributes=True)

    funcionario_id: int
    persona_id: int
    persona_master_id: int | None = Field(
        default=None, description="Usar para GET /funcionarios/{persona_master_id} y ver el perfil fusionado"
    )
    nombre_completo: str
    nombres: str
    apellidos: str
    cedula: str | None = None
    correo: str | None = None
    telefono: str | None = None
    extension_telefonica: str | None = None
    cargo: str
    dependencia: str
    area: str
    vigente: bool
    fecha_inicio: str | None = None
    fecha_fin: str | None = None


class FuncionarioConsolidadoSchema(BaseModel):
    """Ficha "para mostrar" -- Submodulo 8.11, la misma forma que ya usa
    `GovDataPipelineOrchestrator`/`ConsultarEntidadUseCase` (nunca se
    recalcula, solo se serializa)."""

    model_config = ConfigDict(from_attributes=True)

    nombre_completo: str
    cedula: str | None = None
    correo: str | None = None
    telefono: str | None = None
    extension_telefonica: str | None = None
    celular: str | None = None
    correo_personal: str | None = None
    cargo: str | None = None
    dependencia: str | None = None
    registro_foro: str | None = None
    estado_foro: str | None = None
    provincia_foro: str | None = None
    fecha_consulta: str | None = None


class PerfilConsolidadoResponseSchema(BaseModel):
    """`GET /funcionarios/{persona_master_id}` -- forma EXACTA de
    `PerfilConsolidadoDTO` (Submodulo 8.10): `{"persona": {}, "transparencia":
    {}, "senescyt": {}, "foro": {}}`. Sin reconstruir nada -- solo
    serializa lo que `PerfilConsolidadoService` ya calculo."""

    model_config = ConfigDict(from_attributes=True)

    persona: dict[str, Any]
    transparencia: dict[str, Any] = Field(default_factory=dict)
    senescyt: dict[str, Any] = Field(default_factory=dict)
    foro: dict[str, Any] = Field(default_factory=dict)
    generado_en: datetime
