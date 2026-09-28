"""Regla de dominio: Normalizador Academico -- Submodulo 7.4.

    "Universidad Central"  -> "UNIVERSIDAD CENTRAL"
    "Ing. Sistemas"        -> "INGENIERO EN SISTEMAS"
    "Lic."                 -> "LICENCIADO"

El primer caso no necesita catalogo (la normalizacion basica --
`normalizar_texto`, mayuscula/sin tildes/sin puntuacion -- ya alcanza). El
segundo y tercero SI: son abreviaturas/sinonimos reales que ningun
algoritmo generico puede resolver, por eso viven en YAML (Submodulo 7.5,
"nunca hardcodear"). El catalogo se busca SIEMPRE sobre el valor ya
normalizado; si no hay entrada, el valor normalizado es el resultado
(nunca falla por un termino desconocido).
"""

from __future__ import annotations

from dataclasses import replace

from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.domain.rules.normalizacion import normalizar_texto
from govdata.domain.rules.reglas_academicas import CatalogoNormalizacion, RuleEngineAcademico
from govdata.domain.value_objects.estado_registro_academico import EstadoRegistroAcademico

_ESTADOS_CONOCIDOS = {
    "VIGENTE": EstadoRegistroAcademico.VIGENTE,
    "ACTIVO": EstadoRegistroAcademico.VIGENTE,
    "SUSPENDIDO": EstadoRegistroAcademico.SUSPENDIDO,
    "ANULADO": EstadoRegistroAcademico.ANULADO,
    "ANULADA": EstadoRegistroAcademico.ANULADO,
}


def interpretar_estado_registro(texto: str | None) -> EstadoRegistroAcademico:
    """Traduce el texto libre de `estado` (ya normalizado por SENESCYT o
    por el catalogo) al Value Object -- cualquier valor no reconocido cae
    en `DESCONOCIDO`, nunca falla el pipeline por un estado nuevo que
    SENESCYT empiece a reportar."""
    if not texto:
        return EstadoRegistroAcademico.DESCONOCIDO
    return _ESTADOS_CONOCIDOS.get(normalizar_texto(texto), EstadoRegistroAcademico.DESCONOCIDO)


def _normalizar_con_catalogo(valor: str, catalogo: CatalogoNormalizacion) -> str:
    clave = normalizar_texto(valor)
    return catalogo.canonico_por_sinonimo.get(clave, clave)


def normalizar_titulo(valor: str, reglas: RuleEngineAcademico) -> str:
    return _normalizar_con_catalogo(valor, reglas.titulos)


def normalizar_universidad(valor: str, reglas: RuleEngineAcademico) -> str:
    return _normalizar_con_catalogo(valor, reglas.universidades)


def normalizar_nivel(valor: str, reglas: RuleEngineAcademico) -> str:
    return _normalizar_con_catalogo(valor, reglas.niveles)


def normalizar_persona_academica(dto: PersonaAcademicaDTO, reglas: RuleEngineAcademico) -> PersonaAcademicaDTO:
    """Retorna una copia normalizada de `dto`. `numero_registro` NUNCA se
    normaliza (es un identificador oficial, no texto libre -- alterarlo
    romperia el emparejamiento de titulos entre consultas, Submodulo 7.7)."""
    return replace(
        dto,
        titulo=normalizar_titulo(dto.titulo, reglas),
        institucion=normalizar_universidad(dto.institucion, reglas),
        nivel=normalizar_nivel(dto.nivel, reglas),
        estado=normalizar_texto(dto.estado) if dto.estado else dto.estado,
        modalidad=normalizar_texto(dto.modalidad) if dto.modalidad else dto.modalidad,
        pais=normalizar_texto(dto.pais) if dto.pais else dto.pais,
        area_conocimiento=normalizar_texto(dto.area_conocimiento) if dto.area_conocimiento else dto.area_conocimiento,
        tipo_titulo=normalizar_texto(dto.tipo_titulo) if dto.tipo_titulo else dto.tipo_titulo,
    )
