"""Value Object: EstadoRegistroForo -- estado de la matricula de un
abogado segun el Foro de Abogados (Submodulo 8.7: "Cambio de estado").

Mismo catalogo cerrado que `EstadoRegistroAcademico` (Modulo 7): VIGENTE/
SUSPENDIDO/ANULADO son los estados de ejercicio profesional mas comunes
en un colegio/foro profesional ecuatoriano; DESCONOCIDO cubre cualquier
texto que el HTML del Foro reporte y que el normalizador (8.3) no
reconozca -- nunca falla el pipeline por un estado nuevo."""

from __future__ import annotations

from enum import Enum


class EstadoRegistroForo(str, Enum):
    VIGENTE = "vigente"
    SUSPENDIDO = "suspendido"
    ANULADO = "anulado"
    DESCONOCIDO = "desconocido"
