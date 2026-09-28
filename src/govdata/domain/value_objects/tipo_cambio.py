"""Value Object: TipoCambio -- Submodulo 5.1 (Motor de Comparacion).

Clasifica el resultado de comparar un funcionario entre dos versiones de
un documento. `CAMBIO_MULTIPLE` se usa cuando mas de un campo cambio a la
vez (ej. cargo Y dependencia en el mismo mes) -- en ese caso tambien se
registra una `DiferenciaFuncionario` individual por cada campo afectado,
`CAMBIO_MULTIPLE` es la clasificacion AGREGADA de ese funcionario, no
reemplaza el detalle por campo.
"""

from __future__ import annotations

from enum import Enum


class TipoCambio(str, Enum):
    FUNCIONARIO_NUEVO = "funcionario_nuevo"
    FUNCIONARIO_ELIMINADO = "funcionario_eliminado"
    CAMBIO_CARGO = "cambio_cargo"
    CAMBIO_DEPENDENCIA = "cambio_dependencia"
    CAMBIO_CORREO = "cambio_correo"
    CAMBIO_TELEFONO = "cambio_telefono"
    CAMBIO_AREA = "cambio_area"
    CAMBIO_NOMBRE = "cambio_nombre"
    CAMBIO_APELLIDO = "cambio_apellido"
    CAMBIO_MULTIPLE = "cambio_multiple"
    SIN_CAMBIOS = "sin_cambios"
