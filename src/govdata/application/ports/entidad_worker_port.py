"""Puerto: EntidadWorkerPort.

Abstrae "todo lo necesario para descubrir publicacion+documento de UNA
entidad" (navegador, sesion de base de datos, adaptador, casos de uso)
detras de un unico metodo. Existe para que `PipelineOrchestratorService`
(application layer) pueda repartir trabajo entre hilos SIN conocer
Playwright ni SQLAlchemy: solo conoce este puerto.

Cada implementacion concreta (`infrastructure.scraping.dpe_entidad_worker`)
es propietaria de recursos costosos por hilo (ej. un `BrowserManager` con
su Browser Chromium ya lanzado) que se reutilizan entre llamadas a
`procesar()`, y se liberan explicitamente con `cerrar()`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.application.dto.resultado_descubrimiento_dto import ResultadoDescubrimientoEntidadDTO
from govdata.domain.entities.entidad import Entidad


class EntidadWorkerPort(ABC):
    """Procesa el descubrimiento completo de una entidad, de principio a fin."""

    @abstractmethod
    def procesar(self, entidad: Entidad) -> ResultadoDescubrimientoEntidadDTO: ...

    @abstractmethod
    def cerrar(self) -> None:
        """Libera recursos del worker (navegador, sesion de BD, etc.)."""
