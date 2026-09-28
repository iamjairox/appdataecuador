"""Servicio: ColaTrabajosOrquestadorService -- Submodulos 9.6 (Cola de
Trabajos, PostgreSQL), 9.7 (Reanudacion automatica) y 9.8 (Control de
concurrencia: bloqueo optimista).

La concurrencia REAL (multiples hilos procesando trabajos en paralelo) no
vive aqui -- este servicio esta ligado a UNA `Session` (mismo patron que
`TituloAcademicoService`, etc.) y solo sabe operar la cola desde esa
sesion. El pool de hilos vive en `GovDataPipelineOrchestrator`
(Submodulo 9.1), donde cada hilo abre su PROPIA sesion y, con ella, su
PROPIA instancia de este servicio -- `tomar_atomico` (bloqueo optimista,
Submodulo 9.8) es lo que garantiza que dos hilos nunca proceden con el
MISMO trabajo aunque compitan por 'el' `TrabajoOrquestador` mas
prioritario al mismo tiempo."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from govdata.application.ports.trabajo_orquestador_repository_port import (
    TrabajoOrquestadorRepositoryPort,
)
from govdata.config.logging_config import get_logger
from govdata.domain.entities.trabajo_orquestador import TrabajoOrquestador
from govdata.domain.value_objects.estado_trabajo_orquestador import EstadoTrabajoOrquestador
from govdata.domain.value_objects.nivel_prioridad_ejecucion import NivelPrioridadEjecucion
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador

logger = get_logger(__name__)


class ColaTrabajosOrquestadorService:
    def __init__(
        self,
        repository: TrabajoOrquestadorRepositoryPort,
        ahora_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._ahora_provider = ahora_provider

    def encolar(
        self, tipo: TipoTrabajoOrquestador, parametros: dict[str, Any], politica: str,
        prioridad: NivelPrioridadEjecucion = NivelPrioridadEjecucion.MEDIA, entidad_id: int | None = None,
        max_intentos: int = 3,
    ) -> TrabajoOrquestador:
        cuando = self._ahora_provider()
        trabajo = TrabajoOrquestador(
            tipo=tipo, parametros=parametros, politica=politica, prioridad=prioridad, entidad_id=entidad_id,
            max_intentos=max_intentos, creado_en=cuando, actualizado_en=cuando,
        )
        trabajo.encolar()
        guardado = self._repository.guardar(trabajo)
        logger.info("trabajo_encolado", trabajo_id=str(guardado.id), tipo=tipo.value, prioridad=prioridad.value)
        return guardado

    def tomar_siguiente(self) -> TrabajoOrquestador | None:
        """Recorre los candidatos EN_COLA/REINTENTANDO en orden de
        prioridad (9.5) e intenta el bloqueo optimista (9.8) sobre cada
        uno hasta ganar uno -- nunca se detiene en el primer conflicto,
        porque otro worker legitimamente pudo haberlo tomado un instante
        antes."""
        for candidato in self._repository.listar_pendientes_ordenados_por_prioridad():
            if candidato.id is None:  # pragma: no cover -- garantizado por default_factory=uuid4 en la entidad
                continue
            if self._repository.tomar_atomico(candidato.id, candidato.version_lock):
                # El UPDATE atomico ya persistio estado=EJECUTANDO y
                # version_lock+1 en la base -- se refleja tambien en el
                # objeto en memoria para que quede consistente con lo
                # que ahora existe en BD.
                candidato.tomar(self._ahora_provider())
                logger.info("trabajo_tomado", trabajo_id=str(candidato.id))
                return candidato
            logger.info("trabajo_bloqueo_optimista_perdido", trabajo_id=str(candidato.id))
        return None

    def iniciar_directo(self, trabajo: TrabajoOrquestador) -> TrabajoOrquestador:
        """Transiciona EN_COLA -> EJECUTANDO SIN pasar por el bloqueo
        optimista de `tomar_siguiente` -- para el camino SINCRONO
        (`GovDataPipelineOrchestrator.consultar_entidad`/`actualizar_entidad`),
        donde el propio llamador acaba de crear (o ya es duenio exclusivo
        de) el `TrabajoOrquestador` y no compite con nadie por el."""
        trabajo.tomar(self._ahora_provider())
        return self._repository.guardar(trabajo)

    def marcar_completado(self, trabajo: TrabajoOrquestador) -> TrabajoOrquestador:
        trabajo.completar(self._ahora_provider())
        return self._repository.guardar(trabajo)

    def marcar_error(self, trabajo: TrabajoOrquestador, mensaje: str) -> TrabajoOrquestador:
        trabajo.marcar_error(mensaje, self._ahora_provider())
        return self._repository.guardar(trabajo)

    def reintentar_si_corresponde(self, trabajo: TrabajoOrquestador) -> bool:
        if not trabajo.puede_reintentar:
            return False
        trabajo.registrar_reintento(self._ahora_provider())
        self._repository.guardar(trabajo)
        return True

    def pausar(self, trabajo: TrabajoOrquestador) -> TrabajoOrquestador:
        trabajo.pausar()
        return self._repository.guardar(trabajo)

    def reanudar(self, trabajo: TrabajoOrquestador) -> TrabajoOrquestador:
        trabajo.reanudar()
        return self._repository.guardar(trabajo)

    def cancelar(self, trabajo: TrabajoOrquestador) -> TrabajoOrquestador:
        trabajo.cancelar()
        return self._repository.guardar(trabajo)

    def reanudar_interrumpidos(self) -> int:
        """Submodulo 9.7: "Si el servidor se apaga. Al reiniciar. Debe
        continuar exactamente donde quedo." -- cualquier trabajo que
        quedo en EJECUTANDO (un worker murio a mitad de proceso, sin
        oportunidad de marcarlo COMPLETADO/ERROR) se reencola. Se llama
        UNA vez al arrancar el proceso (ver `GovDataPipelineOrchestrator`)."""
        interrumpidos = self._repository.listar_por_estado(EstadoTrabajoOrquestador.EJECUTANDO)
        for trabajo in interrumpidos:
            trabajo.reanudar()
            self._repository.guardar(trabajo)
            logger.warning("trabajo_reanudado_tras_interrupcion", trabajo_id=str(trabajo.id))
        return len(interrumpidos)

    def buscar_por_id(self, trabajo_id: Any) -> TrabajoOrquestador | None:
        return self._repository.buscar_por_id(trabajo_id)
