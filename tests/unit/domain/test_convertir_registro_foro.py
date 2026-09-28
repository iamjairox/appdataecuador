"""Test de regresion: `registro_foro_a_dto` -- el estado DESCONOCIDO debe
volver a `None` en el DTO (mismo bug de Modulo 7, corregido desde el
inicio en Modulo 8: ver `convertir_titulo_academico.py`)."""

from __future__ import annotations

from govdata.domain.entities.registro_foro import RegistroForo
from govdata.domain.rules.convertir_registro_foro import registro_foro_a_dto
from govdata.domain.value_objects.estado_registro_foro import EstadoRegistroForo


class TestRegistroForoADto:
    def test_estado_desconocido_se_convierte_a_none(self) -> None:
        registro = RegistroForo(persona_master_id=1, clave_registro="r1", registro="R1")
        assert registro.estado == EstadoRegistroForo.DESCONOCIDO
        dto = registro_foro_a_dto(registro)
        assert dto.estado is None

    def test_estado_conocido_se_preserva(self) -> None:
        registro = RegistroForo(
            persona_master_id=1, clave_registro="r1", registro="R1", estado=EstadoRegistroForo.SUSPENDIDO
        )
        dto = registro_foro_a_dto(registro)
        assert dto.estado == "suspendido"

    def test_campos_basicos_se_copian(self) -> None:
        registro = RegistroForo(
            persona_master_id=1, clave_registro="r1", nombre_completo="Juan Perez", registro="R1",
            provincia="Pichincha", cedula="0999999999",
        )
        dto = registro_foro_a_dto(registro)
        assert dto.nombre_completo == "Juan Perez"
        assert dto.registro == "R1"
        assert dto.provincia == "Pichincha"
        assert dto.cedula == "0999999999"
