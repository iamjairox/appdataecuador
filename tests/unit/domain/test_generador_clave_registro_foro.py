"""Tests: generador_clave_registro_foro -- Submodulo 8.5."""

from __future__ import annotations

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.domain.rules.generador_clave_registro_foro import generar_clave_registro


class TestGenerarClaveRegistro:
    def test_con_registro_usa_ese_valor_normalizado(self) -> None:
        dto = RegistroForoDTO(registro="1234-56")
        assert generar_clave_registro(dto) == "registro:1234 56"

    def test_sin_registro_cae_a_hash_determinista(self) -> None:
        dto = RegistroForoDTO(nombre_completo="Juan Perez", provincia="Pichincha", cedula="0999999999")
        clave = generar_clave_registro(dto)
        assert clave.startswith("sin_registro:")

    def test_hash_es_determinista_y_estable(self) -> None:
        dto1 = RegistroForoDTO(nombre_completo="Juan Perez", provincia="Pichincha", cedula="0999999999")
        dto2 = RegistroForoDTO(nombre_completo="juan perez", provincia="pichincha", cedula="0999999999")
        assert generar_clave_registro(dto1) == generar_clave_registro(dto2)

    def test_hash_distinto_para_datos_distintos(self) -> None:
        dto1 = RegistroForoDTO(nombre_completo="Juan Perez", provincia="Pichincha")
        dto2 = RegistroForoDTO(nombre_completo="Ana Gomez", provincia="Guayas")
        assert generar_clave_registro(dto1) != generar_clave_registro(dto2)
