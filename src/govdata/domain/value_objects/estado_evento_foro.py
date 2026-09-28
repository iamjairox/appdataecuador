"""Value Object: EstadoEventoForo -- ciclo de vida de `EventoForo`
(Submodulo 8.7). Cola propia e independiente de `EstadoEventoAcademico`
(Modulo 7) -- mismo criterio de separacion documentado en
`estado_evento_academico.py`."""

from __future__ import annotations

from enum import Enum


class EstadoEventoForo(str, Enum):
    PENDIENTE = "pendiente"
    CONSUMIDO = "consumido"
    PROCESADO = "procesado"
