"""Puerto: QueuePort.

Abstrae la cola de trabajos usada por el orquestador para procesar
entidades en paralelo. Foundation/Modulo 1 provee un adaptador en memoria
solo para pruebas unitarias; el adaptador real de produccion (Redis + RQ
o Celery, decidido en el Modulo de Orquestacion) implementa este mismo
contrato sin tocar los casos de uso.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class QueuePort(ABC):
    """Cola de trabajos para procesamiento distribuido/concurrente."""

    @abstractmethod
    def encolar(self, tarea: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        """Encola una tarea para ejecucion asincrona. Retorna un id de job."""

    @abstractmethod
    def estado(self, job_id: str) -> str:
        """Retorna el estado del job: 'pendiente' | 'en_progreso' | 'exito' | 'fallo'."""
