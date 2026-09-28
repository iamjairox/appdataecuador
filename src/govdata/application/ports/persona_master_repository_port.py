"""Puerto: PersonaMasterRepositoryPort -- Submodulo 6.1.

Persistencia del registro maestro de identidad. Los metodos de busqueda
de candidatas son deliberadamente ESPECIFICOS (por fingerprint exacto,
por fingerprint fonetico, por correo) en vez de un unico `listar_todas`:
acotar el universo de comparacion es responsabilidad de la
infraestructura (indice de base de datos), nunca del Motor de Resolucion
de Identidad (que no hace IO) -- mismo principio que
`PersonaRepositoryPort.buscar_candidatas_por_nombre` (Modulo 1).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from govdata.domain.entities.persona_master import PersonaMaster


class PersonaMasterRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, persona_master: PersonaMaster) -> PersonaMaster:
        """Inserta o actualiza. Retorna la instancia con `id` asignado."""

    @abstractmethod
    def buscar_por_id(self, persona_master_id: int) -> PersonaMaster | None: ...

    @abstractmethod
    def buscar_por_persona_id(self, persona_id: int) -> PersonaMaster | None:
        """Idempotencia del alta (Submodulo 6.1): si la Persona de origen
        (Modulo 1-5) ya tiene una PersonaMaster, nunca se crea otra."""

    @abstractmethod
    def buscar_por_fingerprint_principal(self, fingerprint: str) -> PersonaMaster | None:
        """Deduplicacion EXACTA -- primera senal del Motor de Resolucion
        (Submodulo 6.2)."""

    @abstractmethod
    def buscar_candidatas_por_fingerprint_fonetico(self, fingerprint_fonetico: str) -> list[PersonaMaster]:
        """Acota candidatas por similitud fonetica de nombre -- segunda
        senal, mas amplia que la exacta."""

    @abstractmethod
    def buscar_candidatas_por_correo(self, correo: str) -> list[PersonaMaster]:
        """Acota candidatas por correo -- util cuando el nombre cambio de
        escritura entre fuentes pero el correo se mantuvo."""

    @abstractmethod
    def listar_activas(self, limite: int, offset: int = 0) -> list[PersonaMaster]:
        """Listado paginado (Submodulo 6.19, streaming/batch) para
        procesos que recorren todo el universo de PersonaMaster (ej. cola
        de enriquecimiento masivo)."""

    @abstractmethod
    def contar_activas(self) -> int: ...
