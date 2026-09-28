"""Servicio: CacheForoService -- Submodulo 8.8 (Cache).

"Nunca volver a consultar el Foro si ya fue consultado recientemente. La
politica de expiracion debe ser configurable por YAML." Analogo a
`CacheSenescytService` (Modulo 7) pero especifico de este modulo: consulta
el log DEDICADO `ConsultaForoRepositoryPort` (nunca el generico de Modulo
6 ni el de Modulo 7) para no acoplar el cache de Modulo 8 a tablas de
otro modulo congelado."""

from __future__ import annotations

from datetime import datetime, timedelta

from govdata.application.ports.consulta_foro_repository_port import ConsultaForoRepositoryPort
from govdata.domain.rules.reglas_foro import ReglasCacheForo


class CacheForoService:
    def __init__(self, consulta_repository: ConsultaForoRepositoryPort, reglas: ReglasCacheForo) -> None:
        self._repository = consulta_repository
        self._reglas = reglas

    def debe_consultar(self, persona_master_id: int, ahora: datetime) -> bool:
        ultima = self._repository.ultima_consulta(persona_master_id)
        if ultima is None or ultima.exito is not True or ultima.finalizado_en is None:
            return True
        vigente_hasta = ultima.finalizado_en + timedelta(days=self._reglas.dias_vigencia)
        return ahora >= vigente_hasta
