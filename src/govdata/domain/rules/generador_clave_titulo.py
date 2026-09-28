"""Regla de dominio: clave de identidad de un titulo -- base del
Comparador Academico (Submodulo 7.7).

`numero_registro` (el registro oficial SENESCYT) es, cuando existe, una
clave MUCHO mas fuerte que cualquier fingerprint de nombre: es un
identificador emitido por el propio organismo, unico por titulo. Cuando
no viene informado (respuestas incompletas), se cae a una clave
determinista sobre titulo+institucion+nivel normalizados -- nunca se
inventa un numero de registro.
"""

from __future__ import annotations

import hashlib

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.domain.rules.normalizacion import normalizar_texto


def generar_clave_titulo(persona_academica: PersonaAcademicaDTO) -> str:
    if persona_academica.numero_registro and persona_academica.numero_registro.strip():
        return f"registro:{normalizar_texto(persona_academica.numero_registro)}"

    base = "|".join(
        (
            normalizar_texto(persona_academica.titulo),
            normalizar_texto(persona_academica.institucion),
            normalizar_texto(persona_academica.nivel),
        )
    )
    return f"sin_registro:{hashlib.sha256(base.encode('utf-8')).hexdigest()}"
