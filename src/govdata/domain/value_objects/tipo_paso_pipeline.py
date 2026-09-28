"""Value Object: TipoPasoPipeline -- los 8 pasos del Planificador
(Submodulo 9.3), en el orden EXACTO de la especificacion. Cada paso
delega en un modulo YA CONGELADO (nunca se reimplementa su logica aqui,
ver `planificador.py` y `GovDataPipelineOrchestrator`):

    1. DESCUBRIMIENTO / 2. DESCARGA / 3. EXTRACCION -> MonitoreoContinuoService (Modulo 5)
    4. SENESCYT                                     -> EnriquecimientoAcademicoService (Modulo 7)
    5. FORO                                          -> EnriquecimientoForoService (Modulo 8)
    6. COMPARACION                                   -> interno a los pasos 1-5 (Modulos 5/7/8)
    7. PERFIL                                        -> PerfilConsolidadoService (Modulo 8)
    8. ALERTAS                                        -> interno a los pasos 1-5 (Modulos 5/7/8)
"""

from __future__ import annotations

from enum import Enum


class TipoPasoPipeline(str, Enum):
    IDENTIFICACION = "identificacion"
    MATCHING_IDENTIDAD = "matching_identidad"
    PERSISTENCIA = "persistencia"
    DESCUBRIMIENTO = "descubrimiento"
    DESCARGA = "descarga"
    EXTRACCION = "extraccion"
    SENESCYT = "senescyt"
    FORO = "foro"
    COMPARACION = "comparacion"
    PERFIL = "perfil"
    ALERTAS = "alertas"
