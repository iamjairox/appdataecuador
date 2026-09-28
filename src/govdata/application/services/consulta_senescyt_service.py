"""Servicio: ConsultaSenescytService -- Submodulo 7.15 (Auditoria)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from govdata.application.ports.consulta_senescyt_repository_port import (
    ConsultaSenescytRepositoryPort,
)
from govdata.domain.entities.consulta_senescyt import ConsultaSenescyt


class ConsultaSenescytService:
    def __init__(
        self,
        consulta_repository: ConsultaSenescytRepositoryPort,
        ahora_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = consulta_repository
        self._ahora_provider = ahora_provider

    def iniciar(self, persona_master_id: int) -> ConsultaSenescyt:
        consulta = ConsultaSenescyt(persona_master_id=persona_master_id, iniciado_en=self._ahora_provider())
        return self._repository.guardar(consulta)

    def finalizar(
        self,
        consulta: ConsultaSenescyt,
        exito: bool,
        error: str | None = None,
        version_resultante: int | None = None,
        respuesta_cruda: dict[str, Any] | None = None,
        cache_utilizado: bool = False,
    ) -> ConsultaSenescyt:
        cuando = self._ahora_provider()
        duracion = (cuando - consulta.iniciado_en).total_seconds()
        consulta.finalizar(
            exito=exito, cuando=cuando, duracion_segundos=duracion, error=error,
            version_resultante=version_resultante, respuesta_cruda=respuesta_cruda, cache_utilizado=cache_utilizado,
        )
        return self._repository.guardar(consulta)

    def registrar_reintento(self, consulta: ConsultaSenescyt) -> None:
        consulta.registrar_reintento()

    def ultima_consulta(self, persona_master_id: int) -> ConsultaSenescyt | None:
        return self._repository.ultima_consulta(persona_master_id)
