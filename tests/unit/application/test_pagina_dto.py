"""Tests: PaginaDTO -- Modulo 10."""

from __future__ import annotations

from govdata.application.dto.pagina_dto import PaginaDTO


class TestPaginaDTO:
    def test_pages_redondea_hacia_arriba(self) -> None:
        pagina = PaginaDTO(items=[1, 2], page=1, page_size=2, total=5)
        assert pagina.pages == 3

    def test_pages_exacto(self) -> None:
        pagina = PaginaDTO(items=[], page=1, page_size=10, total=20)
        assert pagina.pages == 2

    def test_pages_sin_resultados(self) -> None:
        assert PaginaDTO(items=[], page=1, page_size=10, total=0).pages == 0

    def test_pages_con_page_size_cero_no_divide_por_cero(self) -> None:
        assert PaginaDTO(items=[], page=1, page_size=0, total=5).pages == 0

    def test_defaults(self) -> None:
        pagina: PaginaDTO[int] = PaginaDTO()
        assert pagina.items == []
        assert pagina.page == 1
        assert pagina.page_size == 50
        assert pagina.total == 0
        assert pagina.pages == 0
