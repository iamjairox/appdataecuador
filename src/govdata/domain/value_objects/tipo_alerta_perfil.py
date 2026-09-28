"""Value Object: TipoAlertaPerfil -- Submodulo 6.13 (Alertas de perfil).

Deliberadamente separado de `TipoAlerta` (Modulo 5, `domain/entities/
alerta.py`): aquellas alertas describen cambios de UN funcionario dentro
de UNA entidad publica (DPE); estas describen cambios en el PERFIL
consolidado de una Persona a traves de MULTIPLES fuentes -- dominios
distintos, aunque el nombre se parezca.
"""

from __future__ import annotations

from enum import Enum


class TipoAlertaPerfil(str, Enum):
    TITULO_CAMBIADO = "titulo_cambiado"
    NUEVA_MAESTRIA = "nueva_maestria"
    NUEVA_ESPECIALIZACION = "nueva_especializacion"
    CAMBIO_CORREO_PERFIL = "cambio_correo_perfil"
    NUEVA_INSTITUCION = "nueva_institucion"
    CAMBIO_PROFESION = "cambio_profesion"
