"""Value Object: EstadoEventoAcademico -- ciclo de vida de `EventoAcademico`
(Submodulo 7.9). Cola propia e independiente de `EstadoEvento` (Modulo 5)
y `EstadoEventoPerfil` (Modulo 6) -- mismo criterio de separacion
documentado en `estado_evento_perfil.py`."""

from __future__ import annotations

from enum import Enum


class EstadoEventoAcademico(str, Enum):
    PENDIENTE = "pendiente"
    CONSUMIDO = "consumido"
    PROCESADO = "procesado"
