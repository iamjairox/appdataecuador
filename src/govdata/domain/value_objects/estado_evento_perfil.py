"""Value Object: EstadoEventoPerfil -- ciclo de vida de `EventoPerfil`
(Submodulo 6.12), identico en espiritu al de `EstadoEvento` (Modulo 5)
pero deliberadamente duplicado como enum propio: Modulo 6 no debe
acoplarse al tipo de Modulo 5 solo porque el nombre coincide -- son
colas de eventos independientes (una por Entidad+Documento, otra por
Persona consolidada) que un futuro consumidor (n8n) leera por separado.
"""

from __future__ import annotations

from enum import Enum


class EstadoEventoPerfil(str, Enum):
    PENDIENTE = "pendiente"
    CONSUMIDO = "consumido"
    PROCESADO = "procesado"
