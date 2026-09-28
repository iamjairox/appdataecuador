"""Servicio: CacheSenescytService -- Submodulo 7.10 (Cache por Persona).

"No consultar SENESCYT cada vez." Analogo a `CacheFuenteService` (Modulo
6) pero especifico de este modulo: consulta el log DEDICADO
`ConsultaSenescytRepositoryPort` (nunca el generico de Modulo 6) para no
acoplar el cache de Modulo 7 a tablas de otro modulo congelado.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from govdata.application.ports.consulta_senescyt_repository_port import (
    ConsultaSenescytRepositoryPort,
)
from govdata.domain.rules.reglas_academicas import ReglasCacheSenescyt


class CacheSenescytService:
    def __init__(
        self, consulta_repository: ConsultaSenescytRepositoryPort, reglas: ReglasCacheSenescyt
    ) -> None:
        self._repository = consulta_repository
        self._reglas = reglas

    def debe_consultar(self, persona_master_id: int, ahora: datetime) -> bool:
        ultima = self._repository.ultima_consulta(persona_master_id)
        if ultima is None or ultima.exito is not True or ultima.finalizado_en is None:
            return True
        vigente_hasta = ultima.finalizado_en + timedelta(days=self._reglas.dias_vigencia)
        return ahora >= vigente_hasta
