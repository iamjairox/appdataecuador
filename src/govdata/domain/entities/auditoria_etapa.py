"""Entidad de dominio: AuditoriaEtapa -- Submodulos 9.10 (Monitoreo:
"Registrar cada etapa. Inicio. Fin. Duracion. Errores. Cantidad de
registros.") y 9.15 (Auditoria completa: "cada modulo ejecutado, modulos
omitidos, razon de omision, cache utilizada, versiones utilizadas, tiempo
por etapa, tiempo total").

Ambos submodulos piden exactamente el mismo dato -- una fila por PASO del
Planificador (Submodulo 9.3) ejecutado para UN `TrabajoOrquestador` -- por
eso una unica entidad los satisface a los dos, en vez de duplicar tablas
identicas bajo dos nombres distintos (decision documentada)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from govdata.domain.exceptions.domain_exceptions import AuditoriaEtapaInvalidaError
from govdata.domain.value_objects.estado_paso import EstadoPaso
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline


@dataclass(slots=True)
class AuditoriaEtapa:
    """Registro de auditoria de UN paso del pipeline dinamico, para UN
    `TrabajoOrquestador`."""

    trabajo_orquestador_id: str
    tipo_paso: TipoPasoPipeline
    estado_paso: EstadoPaso
    iniciado_en: datetime
    id: int | None = None
    finalizado_en: datetime | None = None
    razon_omision: str | None = None
    cantidad_registros: int = 0
    error: str | None = None
    cache_utilizada: bool = False
    version_utilizada: str | None = None

    def __post_init__(self) -> None:
        if self.estado_paso == EstadoPaso.OMITIDO and not self.razon_omision:
            raise AuditoriaEtapaInvalidaError(
                f"Un paso OMITIDO ({self.tipo_paso.value}) requiere razon_omision (Submodulo 9.15)"
            )
        if self.finalizado_en is not None and self.finalizado_en < self.iniciado_en:
            raise AuditoriaEtapaInvalidaError("finalizado_en no puede ser anterior a iniciado_en")

    @property
    def duracion_segundos(self) -> float | None:
        if self.finalizado_en is None:
            return None
        return (self.finalizado_en - self.iniciado_en).total_seconds()
