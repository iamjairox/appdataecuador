"""Servicio: ConsultaForoService -- Submodulo 8.17 (Auditoria)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from govdata.application.ports.consulta_foro_repository_port import ConsultaForoRepositoryPort
from govdata.domain.entities.consulta_foro import ConsultaForo


class ConsultaForoService:
    def __init__(
        self,
        consulta_repository: ConsultaForoRepositoryPort,
        ahora_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = consulta_repository
        self._ahora_provider = ahora_provider

    def iniciar(self, persona_master_id: int, job_id: str | None = None, usuario: str = "sistema") -> ConsultaForo:
        consulta = ConsultaForo(
            persona_master_id=persona_master_id, iniciado_en=self._ahora_provider(), job_id=job_id, usuario=usuario,
        )
        return self._repository.guardar(consulta)

    def finalizar(
        self,
        consulta: ConsultaForo,
        exito: bool,
        error: str | None = None,
        version_resultante: int | None = None,
        respuesta_cruda: dict[str, Any] | None = None,
        cache_utilizado: bool = False,
        codigo_http: int | None = None,
        captcha_detectado: bool = False,
        pagina_vacia: bool = False,
    ) -> ConsultaForo:
        cuando = self._ahora_provider()
        duracion = (cuando - consulta.iniciado_en).total_seconds()
        consulta.finalizar(
            exito=exito, cuando=cuando, duracion_segundos=duracion, error=error,
            version_resultante=version_resultante, respuesta_cruda=respuesta_cruda, cache_utilizado=cache_utilizado,
            codigo_http=codigo_http, captcha_detectado=captcha_detectado, pagina_vacia=pagina_vacia,
        )
        return self._repository.guardar(consulta)

    def registrar_reintento(self, consulta: ConsultaForo) -> None:
        consulta.registrar_reintento()

    def ultima_consulta(self, persona_master_id: int) -> ConsultaForo | None:
        return self._repository.ultima_consulta(persona_master_id)
