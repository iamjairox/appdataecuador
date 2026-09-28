"""Regla de dominio: clave de identidad de un registro del Foro -- base
del Comparador Foro (Submodulo 8.5).

`registro` (la matricula/numero de registro oficial del Foro) es, cuando
existe, una clave MUCHO mas fuerte que cualquier fingerprint de nombre:
es un identificador emitido por el propio colegio profesional, unico por
abogado. Cuando no viene informado (HTML incompleto, o el Foro todavia no
asigno numero), se cae a una clave determinista sobre
nombre_completo+provincia normalizados -- nunca se inventa un numero de
registro (Submodulo 8.4)."""

from __future__ import annotations

import hashlib

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.domain.rules.normalizacion import normalizar_texto


def generar_clave_registro(registro_foro: RegistroForoDTO) -> str:
    if registro_foro.registro and registro_foro.registro.strip():
        return f"registro:{normalizar_texto(registro_foro.registro)}"

    base = "|".join(
        (
            normalizar_texto(registro_foro.nombre_completo or ""),
            normalizar_texto(registro_foro.provincia or ""),
            normalizar_texto(registro_foro.cedula or ""),
        )
    )
    return f"sin_registro:{hashlib.sha256(base.encode('utf-8')).hexdigest()}"
