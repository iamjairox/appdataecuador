"""Regla de dominio: Comparador Foro -- Submodulo 8.5.

Empareja registros del Foro entre dos snapshots (anterior/actual) en DOS
pasadas, mismo espiritu exacto que el Comparador Academico (Modulo 7):

    1. Clave PRIMARIA (`generar_clave_registro`): `registro` cuando
       existe -- un identificador oficial, fuerte por si solo.
    2. Clave de RESPALDO (nombre_completo+provincia+cedula normalizados)
       para lo que no emparejo en el paso 1 -- captura el caso real
       "el Foro muestra el perfil SIN numero de registro (matricula en
       tramite) y luego CON uno asignado": sin este respaldo, ese caso se
       veria como dato-eliminado + dato-nuevo, perdiendo el historial
       (viola 8.6, "nunca eliminar informacion previa").

Cuando el respaldo empareja un registro cuya CLAVE cambio, la diferencia
viaja con `clave_registro` (la nueva) Y `clave_registro_anterior` (para
que quien persiste el historial, `RegistroForoService`, sepa bajo que
fila buscar la version a cerrar).

Detecta las categorias del Submodulo 8.5/8.7. A diferencia de Modulo 7
(`CAMBIO_MULTIPLE` explicito), aqui el propio catch-all de la
especificacion ("cambio de CUALQUIER dato del Foro") ya cubre tanto un
campo secundario sin categoria dedicada como 2+ campos a la vez --
`CAMBIO_DATO` -- decision documentada en `tipo_cambio_foro.py`.
"""

from __future__ import annotations

from govdata.application.dto.diferencia_registro_foro_dto import (
    CampoModificadoForoDTO,
    DiferenciaRegistroForoDTO,
)
from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.domain.rules.generador_clave_registro_foro import generar_clave_registro
from govdata.domain.rules.normalizacion import normalizar_texto
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo

_CAMPOS_COMPARABLES = ("nombre_completo", "provincia", "estado", "registro", "cedula", "correo", "celular")
_TIPO_CAMBIO_POR_CAMPO: dict[str, TipoCambioForo] = {
    "provincia": TipoCambioForo.CAMBIO_PROVINCIA,
    "estado": TipoCambioForo.CAMBIO_ESTADO,
    "registro": TipoCambioForo.CAMBIO_REGISTRO,
}
_CAMPOS_INSENSIBLES_A_FORMATO = frozenset({"nombre_completo", "provincia", "estado"})
"""`estado` entra aqui por el mismo motivo que en Modulo 7
(`comparador_academico.py`): `RegistroForo.estado` se reconstruye desde
el Value Object `EstadoRegistroForo` (minusculas) al convertirlo de
vuelta a `RegistroForoDTO` (`convertir_registro_foro.py`), mientras que
una respuesta fresca del Foro llega normalizada en MAYUSCULAS
(`normalizador_foro.py`) -- comparar sin normalizar generaria un falso
`CAMBIO_ESTADO` en CADA consulta, incluso sin cambio real."""


def _clave_respaldo(registro_foro: RegistroForoDTO) -> str:
    return "|".join(
        (
            normalizar_texto(registro_foro.nombre_completo or ""),
            normalizar_texto(registro_foro.provincia or ""),
            normalizar_texto(registro_foro.cedula or ""),
        )
    )


def _valores_difieren(campo: str, anterior: str | None, actual: str | None) -> bool:
    if campo in _CAMPOS_INSENSIBLES_A_FORMATO:
        anterior_norm = normalizar_texto(anterior) if isinstance(anterior, str) else anterior
        actual_norm = normalizar_texto(actual) if isinstance(actual, str) else actual
        return anterior_norm != actual_norm
    return anterior != actual


def _comparar_campos(anterior: RegistroForoDTO, actual: RegistroForoDTO) -> tuple[CampoModificadoForoDTO, ...]:
    campos = []
    for campo in _CAMPOS_COMPARABLES:
        valor_anterior = getattr(anterior, campo)
        valor_actual = getattr(actual, campo)
        if _valores_difieren(campo, valor_anterior, valor_actual):
            campos.append(CampoModificadoForoDTO(campo=campo, valor_anterior=valor_anterior, valor_nuevo=valor_actual))
    return tuple(campos)


def _clasificar(campos_modificados: tuple[CampoModificadoForoDTO, ...]) -> TipoCambioForo:
    if not campos_modificados:
        return TipoCambioForo.SIN_CAMBIOS
    if len(campos_modificados) == 1 and campos_modificados[0].campo in _TIPO_CAMBIO_POR_CAMPO:
        return _TIPO_CAMBIO_POR_CAMPO[campos_modificados[0].campo]
    return TipoCambioForo.CAMBIO_DATO


def _diferencia_par(
    clave_actual: str, anterior: RegistroForoDTO, actual: RegistroForoDTO, clave_anterior: str
) -> DiferenciaRegistroForoDTO:
    campos_modificados = _comparar_campos(anterior, actual)
    return DiferenciaRegistroForoDTO(
        tipo_cambio=_clasificar(campos_modificados),
        clave_registro=clave_actual,
        clave_registro_anterior=clave_anterior if clave_anterior != clave_actual else None,
        datos_actuales=actual,
        datos_anteriores=anterior,
        campos_modificados=campos_modificados,
    )


def comparar_registros(
    anteriores: list[RegistroForoDTO], actuales: list[RegistroForoDTO]
) -> list[DiferenciaRegistroForoDTO]:
    anteriores_por_clave = {generar_clave_registro(r): r for r in anteriores}
    actuales_por_clave = {generar_clave_registro(r): r for r in actuales}

    claves_coincidentes = set(anteriores_por_clave) & set(actuales_por_clave)
    diferencias: list[DiferenciaRegistroForoDTO] = [
        _diferencia_par(clave, anteriores_por_clave[clave], actuales_por_clave[clave], clave)
        for clave in claves_coincidentes
    ]

    anteriores_restantes = {k: v for k, v in anteriores_por_clave.items() if k not in claves_coincidentes}
    actuales_restantes = {k: v for k, v in actuales_por_clave.items() if k not in claves_coincidentes}

    # Paso 2: respaldo por nombre_completo+provincia+cedula, para lo que
    # no empare jo por clave primaria (tipicamente: broto/cambio `registro`).
    anteriores_por_respaldo = {_clave_respaldo(r): (clave, r) for clave, r in anteriores_restantes.items()}
    claves_anteriores_usadas: set[str] = set()
    claves_actuales_usadas: set[str] = set()

    for clave_actual, r_actual in actuales_restantes.items():
        respaldo = _clave_respaldo(r_actual)
        candidato = anteriores_por_respaldo.get(respaldo)
        if candidato is None:
            continue
        clave_anterior, r_anterior = candidato
        diferencias.append(_diferencia_par(clave_actual, r_anterior, r_actual, clave_anterior))
        claves_anteriores_usadas.add(clave_anterior)
        claves_actuales_usadas.add(clave_actual)
        del anteriores_por_respaldo[respaldo]  # cada anterior se consume una sola vez

    for clave, actual in actuales_restantes.items():
        if clave not in claves_actuales_usadas:
            diferencias.append(
                DiferenciaRegistroForoDTO(tipo_cambio=TipoCambioForo.DATO_NUEVO, clave_registro=clave, datos_actuales=actual)
            )

    for clave, anterior in anteriores_restantes.items():
        if clave not in claves_anteriores_usadas:
            diferencias.append(
                DiferenciaRegistroForoDTO(
                    tipo_cambio=TipoCambioForo.DATO_ELIMINADO, clave_registro=clave, datos_anteriores=anterior
                )
            )

    return diferencias
