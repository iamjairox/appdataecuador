"""Servicio: CacheFuenteService -- Submodulo 6.8 (Cache Inteligente por
Fuente).

"Si hash igual + version igual + fecha vigente -> no volver a comparar."
Aqui se traduce a: "si la ultima consulta EXITOSA a esta fuente para esta
PersonaMaster todavia esta dentro de su vigencia (configurable por
fuente), no volver a consultar." Una consulta fallida (`exito=False`) o
inexistente NUNCA bloquea un reintento -- el cache protege contra
re-consultar de mas, jamas contra reintentar un fallo real.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from govdata.application.ports.consulta_fuente_log_repository_port import (
    ConsultaFuenteLogRepositoryPort,
)
from govdata.domain.rules.reglas_identidad import ReglasCachePorFuente
from govdata.domain.value_objects.fuente_externa import FuenteExterna


class CacheFuenteService:
    def __init__(
        self, consulta_fuente_log_repository: ConsultaFuenteLogRepositoryPort, reglas: ReglasCachePorFuente
    ) -> None:
        self._repository = consulta_fuente_log_repository
        self._reglas = reglas

    def debe_consultar(self, persona_master_id: int, fuente: FuenteExterna, ahora: datetime) -> bool:
        ultima = self._repository.ultima_consulta(persona_master_id, fuente)
        if ultima is None or ultima.exito is not True or ultima.finalizado_en is None:
            return True
        dias_vigencia = self._reglas.dias_vigencia(fuente.value)
        vigente_hasta = ultima.finalizado_en + timedelta(days=dias_vigencia)
        return ahora >= vigente_hasta
