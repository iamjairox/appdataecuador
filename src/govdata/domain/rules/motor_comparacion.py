"""Regla de dominio: Motor de Comparacion -- Submodulo 5.1.

Compara la lista de funcionarios de la version ANTERIOR de un documento
contra la version ACTUAL, y produce una `DiferenciaFuncionarioDTO` por
cada funcionario involucrado (nuevo, eliminado, cambiado o sin cambios).

Estrategia de emparejamiento (deliberadamente NUNCA solo por nombre, tal
como exige el cliente):

    1. Fingerprint (Submodulo 4.4) -- señal primaria, exacta. Si dos
       funcionarios comparten fingerprint, son la misma persona.
    2. Correo -- señal de RESPALDO, solo para lo que quedo SIN emparejar
       en el paso 1. Esto es lo unico que permite detectar CAMBIO_NOMBRE /
       CAMBIO_APELLIDO: si el nombre se corrigio (ej. un tilde, un
       apellido mal escrito), el fingerprint cambia por definicion (se
       deriva del nombre), pero el correo institucional tipicamente no.
    3. Lo que sigue sin emparejar tras ambos pasos es, por definicion,
       FUNCIONARIO_NUEVO (solo en la version actual) o
       FUNCIONARIO_ELIMINADO (solo en la version anterior).

Nunca compara `score` (confianza de clasificacion): es una propiedad del
proceso de extraccion, no del mundo real, compararla generaria ruido.

`nombre`/`apellido` se comparan de forma INSENSIBLE a mayusculas/tildes
(via `normalizar_texto`, la misma normalizacion de `NombreCompleto`):
cuando el snapshot "anterior" se reconstruye desde lo YA PERSISTIDO
(`Persona.nombre_completo`, siempre en MAYUSCULAS sin tildes) y el
snapshot "actual" viene de una extraccion fresca (texto tal cual aparece
en el documento, sin esa normalizacion), una comparacion exacta
marcaria a CADA persona sin cambios reales como "cambio de nombre" --
puro ruido de formato, no un cambio real. El valor GUARDADO en el
`CampoModificadoDTO` sigue siendo el texto real (sin normalizar), solo
la DECISION de si hay diferencia usa el texto normalizado.
"""

from __future__ import annotations

from govdata.application.dto.diferencia_dto import CampoModificadoDTO, DiferenciaFuncionarioDTO
from govdata.application.dto.estadisticas_comparacion_dto import EstadisticasComparacionDTO
from govdata.application.dto.resultado_unificado_dto import FuncionarioUnificadoDTO
from govdata.domain.rules.normalizacion import normalizar_texto
from govdata.domain.value_objects.tipo_cambio import TipoCambio

_CAMPOS_COMPARABLES: tuple[str, ...] = (
    "nombre",
    "apellido",
    "cargo",
    "dependencia",
    "correo",
    "telefono",
    "area",
)

_CAMPOS_INSENSIBLES_A_FORMATO: frozenset[str] = frozenset({"nombre", "apellido"})


def _valores_difieren(campo: str, valor_anterior: str | None, valor_nuevo: str | None) -> bool:
    if campo in _CAMPOS_INSENSIBLES_A_FORMATO:
        anterior_norm = normalizar_texto(valor_anterior) if valor_anterior else ""
        nuevo_norm = normalizar_texto(valor_nuevo) if valor_nuevo else ""
        return anterior_norm != nuevo_norm
    return valor_anterior != valor_nuevo

_TIPO_CAMBIO_POR_CAMPO: dict[str, TipoCambio] = {
    "nombre": TipoCambio.CAMBIO_NOMBRE,
    "apellido": TipoCambio.CAMBIO_APELLIDO,
    "cargo": TipoCambio.CAMBIO_CARGO,
    "dependencia": TipoCambio.CAMBIO_DEPENDENCIA,
    "correo": TipoCambio.CAMBIO_CORREO,
    "telefono": TipoCambio.CAMBIO_TELEFONO,
    "area": TipoCambio.CAMBIO_AREA,
}


def comparar_funcionarios(
    anteriores: list[FuncionarioUnificadoDTO], actuales: list[FuncionarioUnificadoDTO]
) -> list[DiferenciaFuncionarioDTO]:
    """Compara dos snapshots de funcionarios y devuelve una diferencia por
    cada persona involucrada en cualquiera de los dos lados."""
    anteriores_por_fp = {f.fingerprint: f for f in anteriores}
    actuales_por_fp = {f.fingerprint: f for f in actuales}

    fps_comunes = set(anteriores_por_fp) & set(actuales_por_fp)
    diferencias = [_comparar_par(anteriores_por_fp[fp], actuales_por_fp[fp]) for fp in fps_comunes]

    anteriores_restantes = {fp: f for fp, f in anteriores_por_fp.items() if fp not in fps_comunes}
    actuales_restantes = {fp: f for fp, f in actuales_por_fp.items() if fp not in fps_comunes}

    # Paso 2: emparejamiento de respaldo por correo (detecta cambio de nombre/apellido).
    anteriores_por_correo = {f.correo: f for f in anteriores_restantes.values() if f.correo}
    fps_actuales_emparejados: set[str] = set()
    fps_anteriores_emparejados: set[str] = set()

    for fp_actual, actual in actuales_restantes.items():
        anterior = anteriores_por_correo.get(actual.correo) if actual.correo else None
        if anterior is not None:
            diferencias.append(_comparar_par(anterior, actual))
            fps_actuales_emparejados.add(fp_actual)
            fps_anteriores_emparejados.add(anterior.fingerprint)

    # Paso 3: lo que sigue sin pareja es nuevo o eliminado.
    for fp_actual, actual in actuales_restantes.items():
        if fp_actual not in fps_actuales_emparejados:
            diferencias.append(_diferencia_extremo(actual, TipoCambio.FUNCIONARIO_NUEVO))

    for fp_anterior, anterior in anteriores_restantes.items():
        if fp_anterior not in fps_anteriores_emparejados:
            diferencias.append(_diferencia_extremo(anterior, TipoCambio.FUNCIONARIO_ELIMINADO))

    return diferencias


def _comparar_par(
    anterior: FuncionarioUnificadoDTO, actual: FuncionarioUnificadoDTO
) -> DiferenciaFuncionarioDTO:
    campos_modificados = [
        CampoModificadoDTO(campo=campo, valor_anterior=getattr(anterior, campo), valor_nuevo=getattr(actual, campo))
        for campo in _CAMPOS_COMPARABLES
        if _valores_difieren(campo, getattr(anterior, campo), getattr(actual, campo))
    ]

    if not campos_modificados:
        tipo = TipoCambio.SIN_CAMBIOS
    elif len(campos_modificados) > 1:
        tipo = TipoCambio.CAMBIO_MULTIPLE
    else:
        tipo = _TIPO_CAMBIO_POR_CAMPO[campos_modificados[0].campo]

    return DiferenciaFuncionarioDTO(
        tipo_cambio=tipo,
        fingerprint=actual.fingerprint,
        nombre=actual.nombre,
        apellido=actual.apellido,
        cargo=actual.cargo,
        dependencia=actual.dependencia,
        correo=actual.correo,
        telefono=actual.telefono,
        area=actual.area,
        campos_modificados=tuple(campos_modificados),
    )


def _diferencia_extremo(funcionario: FuncionarioUnificadoDTO, tipo: TipoCambio) -> DiferenciaFuncionarioDTO:
    return DiferenciaFuncionarioDTO(
        tipo_cambio=tipo,
        fingerprint=funcionario.fingerprint,
        nombre=funcionario.nombre,
        apellido=funcionario.apellido,
        cargo=funcionario.cargo,
        dependencia=funcionario.dependencia,
        correo=funcionario.correo,
        telefono=funcionario.telefono,
        area=funcionario.area,
    )


def calcular_estadisticas(
    diferencias: list[DiferenciaFuncionarioDTO],
    total_anteriores: int,
    total_actuales: int,
    duracion_segundos: float | None = None,
) -> EstadisticasComparacionDTO:
    """Submodulo 5.12 -- calculada UNA sola vez a partir de las diferencias
    ya producidas por `comparar_funcionarios`, nunca recalculada por
    separado (Reporte/Estadisticas/Timeline consumen el mismo resultado)."""
    cantidad_nuevos = sum(1 for d in diferencias if d.tipo_cambio == TipoCambio.FUNCIONARIO_NUEVO)
    cantidad_eliminados = sum(1 for d in diferencias if d.tipo_cambio == TipoCambio.FUNCIONARIO_ELIMINADO)
    cantidad_sin_cambios = sum(1 for d in diferencias if d.tipo_cambio == TipoCambio.SIN_CAMBIOS)
    cantidad_cambios = len(diferencias) - cantidad_nuevos - cantidad_eliminados - cantidad_sin_cambios

    cambios_por_campo: dict[str, int] = dict.fromkeys(_CAMPOS_COMPARABLES, 0)
    for diferencia in diferencias:
        for campo_modificado in diferencia.campos_modificados:
            cambios_por_campo[campo_modificado.campo] = cambios_por_campo.get(campo_modificado.campo, 0) + 1

    # Denominador = union de personas distintas involucradas en CUALQUIERA
    # de los dos lados (== len(diferencias)), no `max(anteriores, actuales)`:
    # con ese ultimo, un turnover COMPLETO (0 personas en comun) podia dar
    # >100% (ej. 3 salen + 3 entran sobre una planta de 3 = "200%"), lo cual
    # no tiene sentido para un porcentaje. Con la union, el peor caso
    # (cero superposicion) da exactamente 100%.
    total_referencia = len(diferencias) or 1
    porcentaje_cambios = (
        (cantidad_nuevos + cantidad_eliminados + cantidad_cambios) / total_referencia
    ) * 100.0

    return EstadisticasComparacionDTO(
        total_funcionarios_anteriores=total_anteriores,
        total_funcionarios_actuales=total_actuales,
        cantidad_nuevos=cantidad_nuevos,
        cantidad_eliminados=cantidad_eliminados,
        cantidad_cambios=cantidad_cambios,
        cantidad_sin_cambios=cantidad_sin_cambios,
        cambios_por_campo=cambios_por_campo,
        porcentaje_cambios=round(porcentaje_cambios, 2),
        duracion_segundos=duracion_segundos,
    )
