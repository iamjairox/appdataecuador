"""Value Object: TipoEventoIdentidad -- Submodulo 6.12 (Eventos)."""

from __future__ import annotations

from enum import Enum


class TipoEventoIdentidad(str, Enum):
    PERSONA_ENRIQUECIDA = "persona_enriquecida"
    PERSONA_FUSIONADA = "persona_fusionada"
    NUEVA_FUENTE = "nueva_fuente"
    CAMBIO_DE_PROFESION = "cambio_de_profesion"
    NUEVO_TITULO = "nuevo_titulo"
    FUENTE_ACTUALIZADA = "fuente_actualizada"
