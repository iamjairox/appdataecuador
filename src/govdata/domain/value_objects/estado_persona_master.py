"""Value Object: EstadoPersonaMaster -- Submodulo 6.1 / 6.21.

    ACTIVA      -- registro maestro vigente y utilizable normalmente.
    EN_REVISION -- existe un `CasoRevisionIdentidad` PENDIENTE_REVISION
                   que involucra a esta PersonaMaster (score 85-97.99%
                   contra otra candidata); se sigue usando con normalidad,
                   pero un futuro dashboard debe poder filtrar estos casos.
    FUSIONADA   -- esta PersonaMaster fue absorbida por otra (perdedora
                   de una fusion automatica o manual); nunca se borra
                   (trazabilidad), solo queda inerte y su `fusionada_en_id`
                   apunta al registro maestro ganador.
"""

from __future__ import annotations

from enum import Enum


class EstadoPersonaMaster(str, Enum):
    ACTIVA = "activa"
    EN_REVISION = "en_revision"
    FUSIONADA = "fusionada"
