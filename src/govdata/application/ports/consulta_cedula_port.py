"""Puerto asíncrono para obtener candidatos de identificación.

El dominio nunca recibe HTML ni conoce Playwright.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.application.dto.identificacion_cedula_dto import CedulaCandidateDTO


class ConsultaCedulaPort(ABC):
    @abstractmethod
    async def consultar_por_nombres(
        self, nombres: str, apellido_paterno: str, apellido_materno: str
    ) -> list[CedulaCandidateDTO]: ...
