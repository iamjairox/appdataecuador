"""Puerto: DescubrimientoPort.

Fachada sobre el pipeline de descubrimiento del Modulo 2 (publicacion +
documento para UNA entidad ya persistida). `ConsultaService` depende de
esta abstraccion, NUNCA de Playwright/`DpeEntidadWorker` directamente --
eso es lo que permite que Modulo 4 reutilice el pipeline de los Modulos
2-3 sin duplicar logica ni romper la regla de dependencia hexagonal.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.application.dto.resultado_descubrimiento_dto import ResultadoDescubrimientoEntidadDTO
from govdata.domain.entities.entidad import Entidad


class DescubrimientoPort(ABC):
    @abstractmethod
    def descubrir(self, entidad: Entidad) -> ResultadoDescubrimientoEntidadDTO: ...

    def cerrar(self) -> None:
        """Libera recursos costosos del adaptador concreto (p. ej. un
        navegador Playwright, FASE 3.8) -- no-op por defecto: los
        adaptadores sin recursos que liberar (fakes de tests, futuros
        adaptadores sin navegador) no necesitan sobreescribirlo."""
        return
