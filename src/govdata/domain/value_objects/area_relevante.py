"""Value Object: AreaRelevante.

Clasifica el area funcional de un cargo publico. ``GENERAL`` conserva los
funcionarios institucionales que no pertenecen a las areas especializadas,
para que el listado del numeral 2 no pierda contactos operativos o directivos.

Este enum sigue siendo la unica fuente de verdad sobre CUALES areas
existen (usado por el esquema de base de datos, `area_relevante_enum`).
El CATALOGO de cargos por area (que antes vivia hardcodeado aqui como
`CARGOS_JERARQUICOS_POR_AREA`) se migro en el Modulo 4 al Motor de Reglas
configurable (`config/rules/clasificacion_areas.yaml`, cargado via
`config.rule_engine.cargar_rule_engine()`) -- ver
`domain.rules.clasificador_funcionarios`. Los valores de este enum
(`"juridica"`, `"financiera"`) coinciden a proposito con las claves de
nivel superior de ese YAML. ``"general"`` es el valor de respaldo cuando
ninguna regla especializada aplica.
"""

from __future__ import annotations

from enum import Enum


class AreaRelevante(str, Enum):
    """Areas de negocio relevantes para la plataforma."""

    JURIDICA = "juridica"
    FINANCIERA = "financiera"
    GENERAL = "general"
