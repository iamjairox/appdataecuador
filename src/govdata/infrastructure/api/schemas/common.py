"""Schemas Pydantic comunes -- Modulo 10, Submodulos 10.8 (paginacion) y
10.11 (errores). `PaginaSchema[T]` es generico (Pydantic v2) para
reutilizarse en cualquier listado paginado sin duplicar la forma."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from govdata.application.dto.pagina_dto import PaginaDTO


class PaginaSchema[T: BaseModel](BaseModel):
    """`{"items": [...], "page": 1, "page_size": 50, "total": 1200, "pages": 24}`."""

    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    page: int
    page_size: int
    total: int
    pages: int

    @classmethod
    def desde_pagina_dto(cls, pagina: PaginaDTO, item_schema: type[T]) -> PaginaSchema[T]:  # type: ignore[type-arg]
        return cls(
            items=[item_schema.model_validate(item) for item in pagina.items],
            page=pagina.page, page_size=pagina.page_size, total=pagina.total, pages=pagina.pages,
        )


class ErrorDetalleSchema(BaseModel):
    codigo: str = Field(description="Codigo de error estable, p.ej. ENTIDAD_NO_ENCONTRADA")
    mensaje: str = Field(description="Mensaje legible, seguro para mostrar al usuario final")
    detalle: str | None = Field(default=None, description="Contexto adicional (nunca un stack trace)")
    request_id: str | None = Field(default=None, description="Correlaciona esta respuesta con los logs del servidor")


class ErrorResponseSchema(BaseModel):
    """`{"error": {"codigo": "...", "mensaje": "...", "detalle": null, "request_id": "..."}}`."""

    error: ErrorDetalleSchema
