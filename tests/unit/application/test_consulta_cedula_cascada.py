"""Tests: consultar_cedula_en_cascada."""

from __future__ import annotations

import asyncio

import pytest

from govdata.application.dto.identificacion_cedula_dto import CedulaCandidateDTO
from govdata.application.ports.consulta_cedula_port import ConsultaCedulaPort
from govdata.application.services.consulta_cedula_cascada import consultar_cedula_en_cascada
from govdata.domain.exceptions.domain_exceptions import GovDataError


class _Fija(ConsultaCedulaPort):
    def __init__(self, valor: list[CedulaCandidateDTO] | Exception) -> None:
        self._valor = valor

    async def consultar_por_nombres(
        self, nombres: str, apellido_paterno: str, apellido_materno: str
    ) -> list[CedulaCandidateDTO]:
        if isinstance(self._valor, Exception):
            raise self._valor
        return list(self._valor)


_OK = [CedulaCandidateDTO("0102030405", "JUAN", "PEREZ")]


def test_devuelve_la_primera_fuente_con_candidatos() -> None:
    resultado = asyncio.run(
        consultar_cedula_en_cascada([_Fija([]), _Fija(_OK)], "JUAN", "PEREZ", "")
    )
    assert resultado == _OK


def test_si_todas_fallan_propaga_el_ultimo_error() -> None:
    with pytest.raises(GovDataError, match="segunda"):
        asyncio.run(
            consultar_cedula_en_cascada(
                [_Fija(GovDataError("primera")), _Fija(GovDataError("segunda"))],
                "JUAN",
                "PEREZ",
                "",
            )
        )


def test_si_responden_vacio_retorna_lista_vacia() -> None:
    resultado = asyncio.run(consultar_cedula_en_cascada([_Fija([]), _Fija([])], "JUAN", "PEREZ", ""))
    assert resultado == []
