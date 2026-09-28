"""Regla de dominio: deteccion de la fila de encabezado -- Submodulo 4.1.

Los documentos publicos no siempre traen el encabezado en la primera fila:
titulos institucionales, logos, filas vacias o celdas combinadas pueden
ocupar las primeras filas de un Excel/CSV, y un libro puede tener varias
hojas (portada, notas, distributivo). Esta regla elige, entre las primeras
filas de cada hoja, la que mas celdas reconoce como encabezado canonico
usando el MISMO mapeo difuso y los MISMOS sinonimos YAML que el
Normalizador Universal (`contar_encabezados_reconocidos`) -- nunca una
lista paralela de palabras clave.

Pura: recibe filas ya leidas (secuencias de celdas), nunca abre archivos.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from govdata.domain.rules.normalizador_universal import contar_encabezados_reconocidos
from govdata.domain.rules.reglas_configurables import ReglasNormalizacion

FILAS_BUSQUEDA_ENCABEZADO = 20
"""Cuantas filas iniciales se inspeccionan buscando el encabezado."""

MINIMO_ENCABEZADOS_RECONOCIDOS = 2
"""Por debajo de esto ninguna fila se considera encabezado confiable y se
conserva el comportamiento historico (primera fila)."""


@dataclass(frozen=True, slots=True)
class EncabezadoDetectado:
    indice_hoja: int
    indice_fila: int
    reconocidos: int


def limpiar_celda_encabezado(valor: object) -> str:
    """`'Apellidos y\\nNombres '` -> `'Apellidos y Nombres'`: los encabezados
    multilinea de Excel llegan con saltos de linea dentro de la celda."""
    if valor is None:
        return ""
    return " ".join(str(valor).split())


def encabezados_unicos(celdas: Sequence[str]) -> tuple[str, ...]:
    """Evita que una columna duplicada pise a la anterior al armar el dict
    de cada fila: la segunda `Correo` pasa a `Correo (2)`. Las celdas
    vacias no se renombran (no mapean a ningun campo)."""
    vistos: dict[str, int] = {}
    resultado: list[str] = []
    for celda in celdas:
        if celda and celda in vistos:
            vistos[celda] += 1
            resultado.append(f"{celda} ({vistos[celda]})")
        else:
            vistos[celda] = 1
            resultado.append(celda)
    return tuple(resultado)


def detectar_fila_encabezado(
    filas: Sequence[Sequence[object]],
    reglas: ReglasNormalizacion,
    minimo_reconocidos: int = MINIMO_ENCABEZADOS_RECONOCIDOS,
) -> EncabezadoDetectado:
    """Indice de la fila con mas encabezados reconocidos. Empates: la
    primera. Si ninguna alcanza `minimo_reconocidos`, fila 0."""
    puntajes = [
        contar_encabezados_reconocidos(tuple(limpiar_celda_encabezado(c) for c in fila), reglas) for fila in filas
    ]
    if not puntajes:
        return EncabezadoDetectado(indice_hoja=0, indice_fila=0, reconocidos=0)
    mejor = max(range(len(puntajes)), key=lambda i: (puntajes[i], -i))
    if puntajes[mejor] < minimo_reconocidos:
        return EncabezadoDetectado(indice_hoja=0, indice_fila=0, reconocidos=puntajes[0])
    return EncabezadoDetectado(indice_hoja=0, indice_fila=mejor, reconocidos=puntajes[mejor])


def seleccionar_hoja_y_encabezado(
    muestras_por_hoja: Sequence[Sequence[Sequence[object]]],
    reglas: ReglasNormalizacion,
    minimo_reconocidos: int = MINIMO_ENCABEZADOS_RECONOCIDOS,
) -> EncabezadoDetectado:
    """Entre varias hojas (en el orden recibido; el llamador pone primero
    la hoja activa), elige la de encabezado mas reconocible. Empates: la
    primera -- asi un libro de una sola hoja se comporta igual que antes."""
    mejor = EncabezadoDetectado(indice_hoja=0, indice_fila=0, reconocidos=-1)
    for indice_hoja, filas in enumerate(muestras_por_hoja):
        deteccion = detectar_fila_encabezado(filas, reglas, minimo_reconocidos)
        if deteccion.reconocidos > mejor.reconocidos:
            mejor = EncabezadoDetectado(indice_hoja, deteccion.indice_fila, deteccion.reconocidos)
    if mejor.reconocidos < 0:
        return EncabezadoDetectado(indice_hoja=0, indice_fila=0, reconocidos=0)
    return mejor
