"""Dobles de prueba (fakes) de los puertos nuevos del Modulo 9."""

from __future__ import annotations

import uuid
from dataclasses import replace

from govdata.application.ports.auditoria_etapa_repository_port import AuditoriaEtapaRepositoryPort
from govdata.application.ports.trabajo_orquestador_repository_port import (
    TrabajoOrquestadorRepositoryPort,
)
from govdata.domain.entities.auditoria_etapa import AuditoriaEtapa
from govdata.domain.entities.trabajo_orquestador import TrabajoOrquestador
from govdata.domain.value_objects.estado_trabajo_orquestador import EstadoTrabajoOrquestador
from govdata.domain.value_objects.nivel_prioridad_ejecucion import NivelPrioridadEjecucion

_ORDEN_PRIORIDAD = {
    NivelPrioridadEjecucion.MUY_ALTA: 3, NivelPrioridadEjecucion.ALTA: 2,
    NivelPrioridadEjecucion.MEDIA: 1, NivelPrioridadEjecucion.BAJA: 0,
}


class FakeTrabajoOrquestadorRepository(TrabajoOrquestadorRepositoryPort):
    def __init__(self) -> None:
        self.guardados: dict[uuid.UUID, TrabajoOrquestador] = {}

    def guardar(self, trabajo: TrabajoOrquestador) -> TrabajoOrquestador:
        self.guardados[trabajo.id] = trabajo
        return trabajo

    def buscar_por_id(self, trabajo_id: uuid.UUID) -> TrabajoOrquestador | None:
        trabajo = self.guardados.get(trabajo_id)
        return replace(trabajo) if trabajo is not None else None

    def listar_por_estado(self, estado: EstadoTrabajoOrquestador, limite: int = 500) -> list[TrabajoOrquestador]:
        return [replace(t) for t in self.guardados.values() if t.estado == estado][:limite]

    def listar_pendientes_ordenados_por_prioridad(self, limite: int = 500) -> list[TrabajoOrquestador]:
        # Copia defensiva -- igual que un `select()` real de SQLAlchemy,
        # que siempre produce objetos Python NUEVOS, independientes de lo
        # que un `UPDATE` (ej. `tomar_atomico`) toque despues en la fila.
        # Sin esta copia, `tomar_atomico` mutaria el MISMO objeto que el
        # llamador todavia sostiene como `candidato`, y la transicion de
        # estado que el llamador aplica despues (`candidato.tomar(...)`)
        # fallaria por partir ya del estado destino.
        candidatos = [
            t for t in self.guardados.values()
            if t.estado in (EstadoTrabajoOrquestador.EN_COLA, EstadoTrabajoOrquestador.REINTENTANDO)
        ]
        ordenados = sorted(candidatos, key=lambda t: _ORDEN_PRIORIDAD[t.prioridad], reverse=True)[:limite]
        return [replace(t) for t in ordenados]

    def contar_por_estado(self) -> dict[EstadoTrabajoOrquestador, int]:
        conteos: dict[EstadoTrabajoOrquestador, int] = {}
        for trabajo in self.guardados.values():
            conteos[trabajo.estado] = conteos.get(trabajo.estado, 0) + 1
        return conteos

    def tomar_atomico(self, trabajo_id: uuid.UUID, version_esperada: int) -> bool:
        trabajo = self.guardados.get(trabajo_id)
        if trabajo is None or trabajo.version_lock != version_esperada:
            return False
        trabajo.estado = EstadoTrabajoOrquestador.EJECUTANDO
        trabajo.version_lock += 1
        return True


class FakeAuditoriaEtapaRepository(AuditoriaEtapaRepositoryPort):
    def __init__(self) -> None:
        self._siguiente_id = 1
        self.guardadas: list[AuditoriaEtapa] = []

    def guardar_lote(self, etapas: list[AuditoriaEtapa]) -> list[AuditoriaEtapa]:
        for etapa in etapas:
            if etapa.id is None:
                etapa.id = self._siguiente_id
                self._siguiente_id += 1
                self.guardadas.append(etapa)
        return etapas

    def listar_por_trabajo(self, trabajo_orquestador_id: str) -> list[AuditoriaEtapa]:
        return [e for e in self.guardadas if e.trabajo_orquestador_id == trabajo_orquestador_id]

    def listar_todo(self, limite: int = 5000) -> list[AuditoriaEtapa]:
        return list(self.guardadas)[:limite]
