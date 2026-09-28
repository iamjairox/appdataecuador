"""Regla de dominio: Comparador Academico -- Submodulo 7.7.

Empareja titulos entre dos snapshots (anterior/actual) en DOS pasadas,
mismo espiritu que el Motor de Comparacion de Funcionarios (Modulo 5,
"nunca unicamente una senal"):

    1. Clave PRIMARIA (`generar_clave_titulo`): `numero_registro` cuando
       existe -- un identificador oficial, fuerte por si solo.
    2. Clave de RESPALDO (titulo+institucion+nivel normalizados) para lo
       que no emparejo en el paso 1 -- captura el caso real de SENESCYT
       "el titulo aparece primero SIN numero de registro (tramite en
       curso) y luego CON uno asignado": sin este respaldo, ese caso se
       veria como titulo-eliminado + titulo-nuevo, perdiendo el
       historial (viola 7.14, "nunca perder historial").

Cuando el respaldo empareja un titulo cuya CLAVE cambio (tipicamente
porque broto un `numero_registro`), la diferencia viaja con
`clave_titulo` (la nueva, la que rige de aqui en adelante) Y
`clave_titulo_anterior` (para que quien persiste el historial,
`TituloAcademicoService`, sepa bajo que fila buscar la version a cerrar).

Detecta las 9 categorias explicitas del Submodulo 7.7. `CAMBIO_MULTIPLE`
se usa tanto para 2+ campos modificados (igual que Modulo 5) como para UN
campo "secundario" (titulo/pais/area_conocimiento/tipo_titulo/
observaciones) que no tiene categoria propia en la especificacion --
decision documentada: nunca se pierde el dato (queda en
`campos_modificados`), solo se agrupa bajo la categoria generica.
"""

from __future__ import annotations

from datetime import date

from govdata.application.dto.diferencia_titulo_dto import (
    CampoModificadoTituloDTO,
    DiferenciaTituloDTO,
)
from govdata.application.dto.persona_academica_dto import PersonaAcademicaDTO
from govdata.domain.rules.generador_clave_titulo import generar_clave_titulo
from govdata.domain.rules.normalizacion import normalizar_texto
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico

_CAMPOS_COMPARABLES = (
    "titulo", "nivel", "institucion", "estado", "modalidad", "numero_registro",
    "pais", "area_conocimiento", "tipo_titulo", "fecha_registro", "fecha_graduacion", "observaciones",
)
_TIPO_CAMBIO_POR_CAMPO: dict[str, TipoCambioAcademico] = {
    "institucion": TipoCambioAcademico.CAMBIO_UNIVERSIDAD,
    "nivel": TipoCambioAcademico.CAMBIO_NIVEL,
    "modalidad": TipoCambioAcademico.CAMBIO_MODALIDAD,
    "numero_registro": TipoCambioAcademico.CAMBIO_REGISTRO,
    "estado": TipoCambioAcademico.CAMBIO_ESTADO,
    "fecha_registro": TipoCambioAcademico.CAMBIO_FECHA,
    "fecha_graduacion": TipoCambioAcademico.CAMBIO_FECHA,
}
_CAMPOS_INSENSIBLES_A_FORMATO = frozenset({"titulo", "institucion", "nivel", "estado"})
"""`estado` entra aqui por el mismo motivo que en Modulo 5
(`motor_comparacion.py`): `TituloAcademico.estado` se reconstruye desde el
Value Object `EstadoRegistroAcademico` (minusculas, ej. "vigente") al
convertirlo de vuelta a `PersonaAcademicaDTO` (`convertir_titulo_academico.py`),
mientras que una respuesta fresca de SENESCYT llega normalizada en
MAYUSCULAS (`normalizador_academico.py`) -- comparar sin normalizar
generaria un falso `CAMBIO_ESTADO` en CADA consulta, incluso sin cambio
real."""


def _clave_respaldo(persona_academica: PersonaAcademicaDTO) -> str:
    return "|".join(
        (
            normalizar_texto(persona_academica.titulo),
            normalizar_texto(persona_academica.institucion),
            normalizar_texto(persona_academica.nivel),
        )
    )


def _texto(valor: str | date | None) -> str | None:
    if valor is None:
        return None
    if isinstance(valor, date):
        return valor.isoformat()
    return valor


def _valores_difieren(campo: str, anterior: str | date | None, actual: str | date | None) -> bool:
    if campo in _CAMPOS_INSENSIBLES_A_FORMATO:
        anterior_norm = normalizar_texto(anterior) if isinstance(anterior, str) else anterior
        actual_norm = normalizar_texto(actual) if isinstance(actual, str) else actual
        return anterior_norm != actual_norm
    return _texto(anterior) != _texto(actual)


def _comparar_campos(
    anterior: PersonaAcademicaDTO, actual: PersonaAcademicaDTO
) -> tuple[CampoModificadoTituloDTO, ...]:
    campos = []
    for campo in _CAMPOS_COMPARABLES:
        valor_anterior = getattr(anterior, campo)
        valor_actual = getattr(actual, campo)
        if _valores_difieren(campo, valor_anterior, valor_actual):
            campos.append(
                CampoModificadoTituloDTO(campo=campo, valor_anterior=_texto(valor_anterior), valor_nuevo=_texto(valor_actual))
            )
    return tuple(campos)


def _clasificar(campos_modificados: tuple[CampoModificadoTituloDTO, ...]) -> TipoCambioAcademico:
    if not campos_modificados:
        return TipoCambioAcademico.SIN_CAMBIOS
    if len(campos_modificados) == 1 and campos_modificados[0].campo in _TIPO_CAMBIO_POR_CAMPO:
        return _TIPO_CAMBIO_POR_CAMPO[campos_modificados[0].campo]
    return TipoCambioAcademico.CAMBIO_MULTIPLE


def _diferencia_par(clave_actual: str, anterior: PersonaAcademicaDTO, actual: PersonaAcademicaDTO, clave_anterior: str) -> DiferenciaTituloDTO:
    campos_modificados = _comparar_campos(anterior, actual)
    return DiferenciaTituloDTO(
        tipo_cambio=_clasificar(campos_modificados),
        clave_titulo=clave_actual,
        clave_titulo_anterior=clave_anterior if clave_anterior != clave_actual else None,
        datos_actuales=actual,
        datos_anteriores=anterior,
        campos_modificados=campos_modificados,
    )


def comparar_titulos(
    anteriores: list[PersonaAcademicaDTO], actuales: list[PersonaAcademicaDTO]
) -> list[DiferenciaTituloDTO]:
    anteriores_por_clave = {generar_clave_titulo(p): p for p in anteriores}
    actuales_por_clave = {generar_clave_titulo(p): p for p in actuales}

    claves_coincidentes = set(anteriores_por_clave) & set(actuales_por_clave)
    diferencias: list[DiferenciaTituloDTO] = [
        _diferencia_par(clave, anteriores_por_clave[clave], actuales_por_clave[clave], clave)
        for clave in claves_coincidentes
    ]

    anteriores_restantes = {k: v for k, v in anteriores_por_clave.items() if k not in claves_coincidentes}
    actuales_restantes = {k: v for k, v in actuales_por_clave.items() if k not in claves_coincidentes}

    # Paso 2: respaldo por titulo+institucion+nivel, para lo que no
    # empare jo por clave primaria (tipicamente: broto/cambio numero_registro).
    anteriores_por_respaldo = {_clave_respaldo(p): (clave, p) for clave, p in anteriores_restantes.items()}
    claves_anteriores_usadas: set[str] = set()
    claves_actuales_usadas: set[str] = set()

    for clave_actual, p_actual in actuales_restantes.items():
        respaldo = _clave_respaldo(p_actual)
        candidato = anteriores_por_respaldo.get(respaldo)
        if candidato is None:
            continue
        clave_anterior, p_anterior = candidato
        diferencias.append(_diferencia_par(clave_actual, p_anterior, p_actual, clave_anterior))
        claves_anteriores_usadas.add(clave_anterior)
        claves_actuales_usadas.add(clave_actual)
        del anteriores_por_respaldo[respaldo]  # cada anterior se consume una sola vez

    for clave, actual in actuales_restantes.items():
        if clave not in claves_actuales_usadas:
            diferencias.append(DiferenciaTituloDTO(tipo_cambio=TipoCambioAcademico.TITULO_NUEVO, clave_titulo=clave, datos_actuales=actual))

    for clave, anterior in anteriores_restantes.items():
        if clave not in claves_anteriores_usadas:
            diferencias.append(
                DiferenciaTituloDTO(tipo_cambio=TipoCambioAcademico.TITULO_ELIMINADO, clave_titulo=clave, datos_anteriores=anterior)
            )

    return diferencias
