"""Value Object: TipoTrabajoOrquestador -- distingue los 6 metodos de
entrada del `GovDataPipelineOrchestrator` (Submodulo 9.1) al persistir un
`TrabajoOrquestador` (Submodulo 9.6)."""

from __future__ import annotations

from enum import Enum


class TipoTrabajoOrquestador(str, Enum):
    VALIDACION_ABOGADO = "validacion_abogado"
    CONSULTA_ENTIDAD = "consulta_entidad"
    CONSULTA_MASIVA = "consulta_masiva"
    CONSULTA_FILTRO = "consulta_filtro"
    ACTUALIZACION_ENTIDAD = "actualizacion_entidad"
    ACTUALIZACION_MASIVA = "actualizacion_masiva"
    REPROCESO = "reproceso"
