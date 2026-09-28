"""DTO: ResultadoComparacionDTO -- Submodulo 5.14, EL CONTRATO OFICIAL del
Motor de Comparacion.

Forma EXACTA pedida por el cliente:

    {
      "entidad": {},
      "documento_anterior": {},
      "documento_actual": {},
      "nuevos": [],
      "eliminados": [],
      "cambios": [],
      "sin_cambios": [],
      "estadisticas": {},
      "alertas": []
    }

Sera el contrato oficial para los modulos 6, 7, API, Dashboard, n8n.
Nunca romper este contrato -- igual que `ResultadoUnificadoDTO` (Modulo
4), cambiar los NOMBRES de estos campos es un cambio incompatible.

`documento_anterior` es `None` cuando la entidad se ve por primera vez
(no hay version previa contra la cual comparar -- en ese caso TODOS los
funcionarios actuales aparecen en `nuevos`, nunca en `cambios`)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

from govdata.application.dto.alerta_dto import AlertaDTO
from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.application.dto.estadisticas_comparacion_dto import EstadisticasComparacionDTO
from govdata.application.dto.resultado_unificado_dto import DocumentoResumenDTO, EntidadResumenDTO


@dataclass(frozen=True, slots=True)
class ResultadoComparacionDTO:
    """`{"entidad": {}, "documento_anterior": {}, "documento_actual": {},
    "nuevos": [], "eliminados": [], "cambios": [], "sin_cambios": [],
    "estadisticas": {}, "alertas": []}`."""

    entidad: EntidadResumenDTO
    documento_anterior: DocumentoResumenDTO | None
    documento_actual: DocumentoResumenDTO
    nuevos: list[DiferenciaFuncionarioDTO] = field(default_factory=list)
    eliminados: list[DiferenciaFuncionarioDTO] = field(default_factory=list)
    cambios: list[DiferenciaFuncionarioDTO] = field(default_factory=list)
    sin_cambios: list[DiferenciaFuncionarioDTO] = field(default_factory=list)
    estadisticas: EstadisticasComparacionDTO | None = None
    alertas: list[AlertaDTO] = field(default_factory=list)
    generado_en: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        """Serializacion exacta del contrato (para logging/API/n8n)."""
        return asdict(self)
