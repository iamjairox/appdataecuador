"""Value Object: FuenteExterna -- Submodulo 6.6 (Fuentes Externas).

Catalogo cerrado de fuentes que el Motor de Identidad sabe reconocer.
Modulo 6 NO implementa ningun adaptador real (esta explicitamente
prohibido por la especificacion: "NO implementar aun SENESCYT") -- solo
declara el vocabulario que usaran los puertos, el cache por fuente
(Submodulo 6.8) y el versionado por fuente (Submodulo 6.9).

DPE se incluye porque los Modulos 1-5 ya son, en si mismos, la primera
fuente de la que la Persona-maestra puede provenir.
"""

from __future__ import annotations

from enum import Enum


class FuenteExterna(str, Enum):
    DPE = "dpe"
    CONSULTAS_ECUADOR = "consultas_ecuador"
    SENESCYT = "senescyt"
    FORO_ABOGADOS = "foro_abogados"
    FUNCION_JUDICIAL = "funcion_judicial"
    SRI = "sri"
    CONTRALORIA = "contraloria"
    REGISTRO_MERCANTIL = "registro_mercantil"
    OTRA = "otra"
