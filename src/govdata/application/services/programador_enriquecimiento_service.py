"""Servicio: ProgramadorEnriquecimientoService -- Submodulo 7.20, mejora 2
sugerida por el cliente: "en vez de depender unicamente de consultas
manuales, ejecutar reglas como revisar perfiles cada 30 dias, revisar
inmediatamente ante un cambio de funcionario, y priorizar personas con
alertas pendientes."

Deliberadamente NO es un daemon/cron: eso requeriria infraestructura
(n8n, scheduler de SO) explicitamente fuera de alcance del Modulo 7
("solo construir el motor"). Este servicio es el MOTOR DE DECISION --
responde "¿que PersonaMaster deben re-enriquecerse ahora, y en que
orden?" -- un futuro job programado (fuera de este modulo) solo necesita
llamarlo periodicamente.

Reutiliza, sin modificarlo, `PriorizacionService` (Modulo 6) para el
orden por cargo -- el mismo motor que ya prioriza el enriquecimiento de
identidad se reutiliza aqui para el academico.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from govdata.application.ports.alerta_academica_repository_port import (
    AlertaAcademicaRepositoryPort,
)
from govdata.application.ports.consulta_senescyt_repository_port import (
    ConsultaSenescytRepositoryPort,
)
from govdata.application.ports.persona_master_repository_port import PersonaMasterRepositoryPort
from govdata.application.services.priorizacion_service import PriorizacionService
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.rules.reglas_academicas import ReglasCacheSenescyt


class ProgramadorEnriquecimientoService:
    def __init__(
        self,
        persona_master_repository: PersonaMasterRepositoryPort,
        consulta_repository: ConsultaSenescytRepositoryPort,
        alerta_repository: AlertaAcademicaRepositoryPort,
        priorizacion_service: PriorizacionService,
        reglas_cache: ReglasCacheSenescyt,
    ) -> None:
        self._persona_master_repository = persona_master_repository
        self._consulta_repository = consulta_repository
        self._alerta_repository = alerta_repository
        self._priorizacion_service = priorizacion_service
        self._reglas_cache = reglas_cache

    def debe_reenriquecerse_ahora(self, persona_master_id: int, ahora: datetime) -> bool:
        """Regla "revisar cada N dias" (por defecto, la vigencia del
        cache, Submodulo 7.10) -- tambien sirve como disparo inmediato
        (regla "ante un cambio de funcionario"): el llamador (ej. un
        futuro listener del Modulo 5) simplemente invoca esto en cuanto
        ocurre el evento que le interesa, sin que este servicio se
        suscriba a nada."""
        ultima = self._consulta_repository.ultima_consulta(persona_master_id)
        if ultima is None or ultima.exito is not True or ultima.finalizado_en is None:
            return True
        vigente_hasta = ultima.finalizado_en + timedelta(days=self._reglas_cache.dias_vigencia)
        return ahora >= vigente_hasta

    def candidatos_a_enriquecer(
        self, ahora: datetime, cargo_por_persona_master: dict[int, str | None] | None = None, limite: int = 500,
    ) -> list[PersonaMaster]:
        """Entre las PersonaMaster activas (Modulo 6, REUTILIZADO), retorna
        las que necesitan re-enriquecerse, con las que tienen alertas
        academicas PENDIENTES siempre primero (regla 3), y dentro de cada
        grupo ordenadas por cargo (Submodulo 6.11, REUTILIZADO) si se
        provee el mapeo."""
        activas = self._persona_master_repository.listar_activas(limite=limite)
        pendientes_de_alerta = {
            a.persona_master_id for a in self._alerta_repository.listar_pendientes(limite=limite)
        }

        candidatas = [pm for pm in activas if pm.id is not None and self.debe_reenriquecerse_ahora(pm.id, ahora)]
        con_alerta = [pm for pm in candidatas if pm.id in pendientes_de_alerta]
        sin_alerta = [pm for pm in candidatas if pm.id not in pendientes_de_alerta]

        if cargo_por_persona_master:
            con_alerta = self._priorizacion_service.priorizar(con_alerta, cargo_por_persona_master)
            sin_alerta = self._priorizacion_service.priorizar(sin_alerta, cargo_por_persona_master)

        return con_alerta + sin_alerta
