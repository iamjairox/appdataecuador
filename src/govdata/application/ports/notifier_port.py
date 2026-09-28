"""Puerto: NotifierPort.

Contrato para alertas (ej. "cambio de Director Juridico detectado"),
consumido por el futuro modulo de monitoreo/alertas. Foundation solo
define el contrato.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class NotifierPort(ABC):
    """Envio de notificaciones/alertas sobre eventos relevantes del pipeline."""

    @abstractmethod
    def notificar(self, titulo: str, mensaje: str, nivel: str = "info") -> None: ...
