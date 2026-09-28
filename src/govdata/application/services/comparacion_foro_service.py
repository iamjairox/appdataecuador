"""Servicio: ComparacionForoService -- orquesta el Comparador Foro
(Submodulo 8.5): obtiene los registros VIGENTES ya persistidos para una
PersonaMaster, los traduce de vuelta a `RegistroForoDTO`, y delega la
comparacion en si al motor de dominio puro."""

from __future__ import annotations

from govdata.application.dto.diferencia_registro_foro_dto import DiferenciaRegistroForoDTO
from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.application.ports.registro_foro_repository_port import RegistroForoRepositoryPort
from govdata.domain.rules.comparador_foro import comparar_registros
from govdata.domain.rules.convertir_registro_foro import registro_foro_a_dto


class ComparacionForoService:
    def __init__(self, registro_repository: RegistroForoRepositoryPort) -> None:
        self._registro_repository = registro_repository

    def comparar(self, persona_master_id: int, actuales: list[RegistroForoDTO]) -> list[DiferenciaRegistroForoDTO]:
        vigentes = self._registro_repository.listar_vigentes_por_persona_master(persona_master_id)
        anteriores = [registro_foro_a_dto(r) for r in vigentes]
        return comparar_registros(anteriores, actuales)
