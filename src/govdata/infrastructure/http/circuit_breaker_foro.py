"""Circuit Breaker del adaptador del Foro de Abogados -- Submodulo 8.9.

Complementa (no reemplaza) el backoff exponencial de
`shared.retry.retry_policy.con_reintentos` (Modulo 1, reutilizado sin
modificar): los reintentos absorben una falla TRANSITORIA dentro de UNA
consulta; el Circuit Breaker protege al Foro (y al resto del sistema) de
seguir insistiendo cuando VARIAS consultas seguidas ya vienen fallando --
evita machacar un servicio caido y da tiempo a que se recupere.

Maquina de 3 estados clasica:

    CERRADO ---(fallos consecutivos >= umbral)---> ABIERTO
    ABIERTO ---(paso el enfriamiento)-------------> SEMI_ABIERTO
    SEMI_ABIERTO ---(exito)-----------------------> CERRADO
    SEMI_ABIERTO ---(fallo)------------------------> ABIERTO
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from enum import Enum

from govdata.config.logging_config import get_logger
from govdata.domain.rules.reglas_foro import ReglasCircuitoForo

logger = get_logger(__name__)


class EstadoCircuito(str, Enum):
    CERRADO = "cerrado"
    ABIERTO = "abierto"
    SEMI_ABIERTO = "semi_abierto"


class CircuitBreakerForo:
    def __init__(
        self, reglas: ReglasCircuitoForo, ahora_provider: Callable[[], datetime] = lambda: datetime.now(UTC)
    ) -> None:
        self._reglas = reglas
        self._ahora_provider = ahora_provider
        self._estado = EstadoCircuito.CERRADO
        self._fallos_consecutivos = 0
        self._abierto_desde: datetime | None = None

    @property
    def estado(self) -> EstadoCircuito:
        return self._estado

    def permitir_intento(self) -> bool:
        if self._estado == EstadoCircuito.CERRADO:
            return True
        if self._estado == EstadoCircuito.SEMI_ABIERTO:
            return True  # un unico intento de prueba

        # ABIERTO: solo se permite pasar a SEMI_ABIERTO tras el enfriamiento.
        if self._abierto_desde is not None:
            transcurrido = (self._ahora_provider() - self._abierto_desde).total_seconds()
            if transcurrido >= self._reglas.segundos_enfriamiento:
                self._estado = EstadoCircuito.SEMI_ABIERTO
                logger.info("circuito_foro_semi_abierto")
                return True
        return False

    def registrar_exito(self) -> None:
        if self._estado != EstadoCircuito.CERRADO:
            logger.info("circuito_foro_cerrado", estado_previo=self._estado.value)
        self._fallos_consecutivos = 0
        self._estado = EstadoCircuito.CERRADO
        self._abierto_desde = None

    def registrar_fallo(self) -> None:
        self._fallos_consecutivos += 1
        if self._estado == EstadoCircuito.SEMI_ABIERTO or self._fallos_consecutivos >= self._reglas.umbral_fallos:
            self._estado = EstadoCircuito.ABIERTO
            self._abierto_desde = self._ahora_provider()
            logger.warning("circuito_foro_abierto", fallos_consecutivos=self._fallos_consecutivos)
