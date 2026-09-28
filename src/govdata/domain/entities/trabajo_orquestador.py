"""Entidad de dominio: TrabajoOrquestador -- Submodulo 9.6 (Cola de
Trabajos, persistida en PostgreSQL, NUNCA Redis) + Submodulo 9.7
(Reanudacion automatica) + Submodulo 9.8 (Control de concurrencia:
bloqueo optimista via `version_lock`).

Maquina de estados:

    PENDIENTE -> EN_COLA -> EJECUTANDO -> COMPLETADO
                    ^            |  \\
                    |            |   -> ERROR -> REINTENTANDO -> EJECUTANDO
                    |            v
                    +------- PAUSADO
    (cualquier estado no terminal) -> CANCELADO

`version_lock` se incrementa en CADA escritura -- el repositorio de
infraestructura (Submodulo 9.8) hace el UPDATE condicionado a
`WHERE id = ? AND version_lock = ?`; si otro worker ya tomo el trabajo
entre la lectura y la escritura, el UPDATE afecta 0 filas y el
repositorio lanza `BloqueoOptimistaFallidoError` -- nunca se procesa la
misma entidad dos veces en paralelo."""

from __future__ import annotations

import uuid as uuid_module
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from govdata.domain.exceptions.domain_exceptions import TrabajoOrquestadorInvalidoError
from govdata.domain.value_objects.estado_trabajo_orquestador import EstadoTrabajoOrquestador
from govdata.domain.value_objects.nivel_prioridad_ejecucion import NivelPrioridadEjecucion
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador

_TRANSICIONES_VALIDAS: dict[EstadoTrabajoOrquestador, set[EstadoTrabajoOrquestador]] = {
    EstadoTrabajoOrquestador.PENDIENTE: {EstadoTrabajoOrquestador.EN_COLA, EstadoTrabajoOrquestador.CANCELADO},
    EstadoTrabajoOrquestador.EN_COLA: {
        EstadoTrabajoOrquestador.EJECUTANDO, EstadoTrabajoOrquestador.PAUSADO, EstadoTrabajoOrquestador.CANCELADO,
    },
    EstadoTrabajoOrquestador.EJECUTANDO: {
        EstadoTrabajoOrquestador.COMPLETADO, EstadoTrabajoOrquestador.ERROR, EstadoTrabajoOrquestador.PAUSADO,
        EstadoTrabajoOrquestador.EN_COLA, EstadoTrabajoOrquestador.CANCELADO,
    },
    EstadoTrabajoOrquestador.PAUSADO: {EstadoTrabajoOrquestador.EN_COLA, EstadoTrabajoOrquestador.CANCELADO},
    EstadoTrabajoOrquestador.ERROR: {EstadoTrabajoOrquestador.REINTENTANDO, EstadoTrabajoOrquestador.CANCELADO},
    EstadoTrabajoOrquestador.REINTENTANDO: {
        EstadoTrabajoOrquestador.EJECUTANDO, EstadoTrabajoOrquestador.EN_COLA, EstadoTrabajoOrquestador.CANCELADO,
    },
    EstadoTrabajoOrquestador.COMPLETADO: set(),
    EstadoTrabajoOrquestador.CANCELADO: set(),
}


@dataclass(slots=True)
class TrabajoOrquestador:
    """Un item de la cola persistente del Orquestador Maestro."""

    tipo: TipoTrabajoOrquestador
    parametros: dict[str, Any] = field(default_factory=dict)
    id: uuid_module.UUID = field(default_factory=uuid_module.uuid4)
    politica: str = "consulta_rapida"
    estado: EstadoTrabajoOrquestador = EstadoTrabajoOrquestador.PENDIENTE
    prioridad: NivelPrioridadEjecucion = NivelPrioridadEjecucion.MEDIA
    version_lock: int = 1
    intentos: int = 0
    max_intentos: int = 3
    entidad_id: int | None = None
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None
    iniciado_en: datetime | None = None
    finalizado_en: datetime | None = None
    ultimo_error: str | None = None

    def __post_init__(self) -> None:
        if self.version_lock < 1:
            raise TrabajoOrquestadorInvalidoError(f"version_lock invalida: {self.version_lock}")
        if self.intentos < 0:
            raise TrabajoOrquestadorInvalidoError("intentos no puede ser negativo")
        if self.max_intentos < 1:
            raise TrabajoOrquestadorInvalidoError("max_intentos debe ser >= 1")

    def _transicionar(self, nuevo_estado: EstadoTrabajoOrquestador) -> None:
        permitidos = _TRANSICIONES_VALIDAS.get(self.estado, set())
        if nuevo_estado not in permitidos:
            raise TrabajoOrquestadorInvalidoError(f"Transicion invalida: {self.estado.value} -> {nuevo_estado.value}")
        self.estado = nuevo_estado
        self.version_lock += 1

    def encolar(self) -> None:
        self._transicionar(EstadoTrabajoOrquestador.EN_COLA)

    def tomar(self, cuando: datetime) -> None:
        """El worker que gano el bloqueo optimista (Submodulo 9.8) marca
        el trabajo como EJECUTANDO."""
        self._transicionar(EstadoTrabajoOrquestador.EJECUTANDO)
        self.iniciado_en = cuando

    def pausar(self) -> None:
        self._transicionar(EstadoTrabajoOrquestador.PAUSADO)

    def reanudar(self) -> None:
        """PAUSADO -> EN_COLA, o el trabajo se reencola tras una
        interrupcion detectada al reiniciar (Submodulo 9.7)."""
        self._transicionar(EstadoTrabajoOrquestador.EN_COLA)

    def registrar_reintento(self, cuando: datetime) -> None:
        if self.intentos + 1 > self.max_intentos:
            raise TrabajoOrquestadorInvalidoError(
                f"Se agoto el presupuesto de reintentos ({self.max_intentos}) para el trabajo {self.id}"
            )
        self.intentos += 1
        self._transicionar(EstadoTrabajoOrquestador.REINTENTANDO)
        self.actualizado_en = cuando

    def completar(self, cuando: datetime) -> None:
        self._transicionar(EstadoTrabajoOrquestador.COMPLETADO)
        self.finalizado_en = cuando

    def marcar_error(self, mensaje: str, cuando: datetime) -> None:
        self._transicionar(EstadoTrabajoOrquestador.ERROR)
        self.ultimo_error = mensaje
        self.finalizado_en = cuando

    def cancelar(self) -> None:
        self._transicionar(EstadoTrabajoOrquestador.CANCELADO)

    @property
    def puede_reintentar(self) -> bool:
        return self.estado == EstadoTrabajoOrquestador.ERROR and self.intentos < self.max_intentos

    @property
    def es_terminal(self) -> bool:
        return self.estado in (EstadoTrabajoOrquestador.COMPLETADO, EstadoTrabajoOrquestador.CANCELADO)
