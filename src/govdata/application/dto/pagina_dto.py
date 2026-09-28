"""DTO: PaginaDTO -- envoltorio generico de paginacion para el Modulo 10
(API REST). Forma EXACTA pedida por el cliente:

    {"items": [...], "page": 1, "page_size": 50, "total": 1200, "pages": 24}

Generico (`[T]`, PEP 695 -- Python 3.13) para reutilizarse en cualquier
listado paginado (funcionarios, entidades, alertas, cambios, ...) sin
duplicar esta forma por cada tipo."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PaginaDTO[T]:
    """`{"items": [...], "page": 1, "page_size": 50, "total": 1200, "pages": 24}`."""

    items: list[T] = field(default_factory=list)
    page: int = 1
    page_size: int = 50
    total: int = 0

    @property
    def pages(self) -> int:
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size
