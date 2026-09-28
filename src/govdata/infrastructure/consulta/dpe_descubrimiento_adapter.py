"""Adaptador: DpeDescubrimientoAdapter -- implementa `DescubrimientoPort`.

Envuelve el `DpeEntidadWorker` del Modulo 2 (reutilizado, NO recreado por
consulta -- mismo navegador para toda la vida de este adaptador) sin
duplicar ninguna logica de descubrimiento.
"""

from __future__ import annotations

from govdata.application.dto.resultado_descubrimiento_dto import ResultadoDescubrimientoEntidadDTO
from govdata.application.ports.descubrimiento_port import DescubrimientoPort
from govdata.domain.entities.entidad import Entidad
from govdata.infrastructure.scraping.dpe_entidad_worker import DpeEntidadWorker


class DpeDescubrimientoAdapter(DescubrimientoPort):
    def __init__(self, worker: DpeEntidadWorker) -> None:
        self._worker = worker

    def descubrir(self, entidad: Entidad) -> ResultadoDescubrimientoEntidadDTO:
        return self._worker.procesar(entidad)

    def cerrar(self) -> None:
        self._worker.cerrar()
