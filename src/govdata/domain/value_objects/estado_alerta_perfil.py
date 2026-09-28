"""Value Object: EstadoAlertaPerfil -- ciclo de vida de `AlertaPerfil`
(Submodulo 6.13). Ver `estado_evento_perfil.py` para la justificacion de
por que se duplica en vez de reutilizar el enum equivalente de Modulo 5."""

from __future__ import annotations

from enum import Enum


class EstadoAlertaPerfil(str, Enum):
    PENDIENTE = "pendiente"
    ENVIADA = "enviada"
    DESCARTADA = "descartada"
