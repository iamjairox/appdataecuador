"""Regla de dominio: segmentacion de un nombre completo en nombres y
apellidos -- Submodulo 4.2.

La plantilla del numeral 2 del portal DPE trae UNA columna "Apellidos y
Nombres" (verificado en 24/24 archivos reales, 2026-09-27); otras fuentes
traen "Nombres y Apellidos" o un encabezado neutro ("Servidor",
"Funcionario"). Dividir siempre "por la mitad, la primera mitad son los
nombres" invertia el nombre en la plantilla estandar: "PEREZ GOMEZ JUAN
CARLOS" quedaba con nombres="PEREZ GOMEZ".

Esta regla:
    1. Deduce el orden del propio encabezado (`detectar_orden_por_encabezado`).
    2. Agrupa particulas de apellidos compuestos ("DE LA CRUZ", "DEL
       POZO") como una sola unidad.
    3. Aplica la convencion ecuatoriana (dos apellidos) solo cuando el
       orden es conocido, e informa una confianza -- nunca inventa
       certeza: con orden desconocido conserva la heuristica historica y
       marca la segmentacion como BAJA.

El texto original nunca se modifica (se reparte palabra por palabra, tal
como vino); la normalizacion solo se usa para comparar.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from govdata.domain.rules.normalizacion import normalizar_texto

_PARTICULAS = frozenset({"DE", "DEL", "LA", "LAS", "LOS", "SAN", "SANTA", "Y", "DA", "DI", "VAN", "VON", "MC"})


class OrdenNombre(str, Enum):
    APELLIDOS_PRIMERO = "apellidos_primero"
    NOMBRES_PRIMERO = "nombres_primero"
    DESCONOCIDO = "desconocido"


class ConfianzaSegmentacion(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


@dataclass(frozen=True, slots=True)
class SegmentacionNombre:
    nombres: str
    apellidos: str
    orden: OrdenNombre
    confianza: ConfianzaSegmentacion


def detectar_orden_por_encabezado(encabezado: str) -> OrdenNombre:
    """'Apellidos y Nombres' -> APELLIDOS_PRIMERO; 'Nombres y Apellidos'
    -> NOMBRES_PRIMERO; 'Servidor' / 'Nombre Completo' -> DESCONOCIDO."""
    palabras = normalizar_texto(encabezado).split()
    posicion_apellido = next((i for i, p in enumerate(palabras) if p.startswith("APELLIDO")), None)
    posicion_nombre = next((i for i, p in enumerate(palabras) if p.startswith("NOMBRE")), None)
    if posicion_apellido is None or posicion_nombre is None:
        return OrdenNombre.DESCONOCIDO
    return OrdenNombre.APELLIDOS_PRIMERO if posicion_apellido < posicion_nombre else OrdenNombre.NOMBRES_PRIMERO


def _unidades(texto: str) -> tuple[list[str], bool]:
    """Palabras del texto original agrupando particulas con la palabra
    siguiente. Retorna (unidades, hubo_particulas)."""
    unidades: list[str] = []
    pendientes: list[str] = []
    hubo_particulas = False
    for palabra in texto.split():
        if normalizar_texto(palabra) in _PARTICULAS:
            pendientes.append(palabra)
            hubo_particulas = True
            continue
        unidades.append(" ".join([*pendientes, palabra]))
        pendientes = []
    if pendientes:  # particula suelta al final ("... DE"): se pega a la ultima unidad
        if unidades:
            unidades[-1] = " ".join([unidades[-1], *pendientes])
        else:
            unidades.append(" ".join(pendientes))
    return unidades, hubo_particulas


def _confianza(cantidad_unidades: int, hubo_particulas: bool) -> ConfianzaSegmentacion:
    if cantidad_unidades == 4 and not hubo_particulas:
        return ConfianzaSegmentacion.ALTA
    if cantidad_unidades in (3, 4, 5):
        return ConfianzaSegmentacion.MEDIA
    return ConfianzaSegmentacion.BAJA


def _dividir_por_la_mitad(texto: str) -> tuple[str, str]:
    palabras = texto.split()
    if len(palabras) <= 1:
        return texto.strip(), ""
    mitad = (len(palabras) + 1) // 2
    return " ".join(palabras[:mitad]), " ".join(palabras[mitad:])


def segmentar_nombre_completo(texto: str, orden: OrdenNombre) -> SegmentacionNombre:
    if orden == OrdenNombre.DESCONOCIDO:
        nombres, apellidos = _dividir_por_la_mitad(texto)
        return SegmentacionNombre(nombres, apellidos, orden, ConfianzaSegmentacion.BAJA)

    unidades, hubo_particulas = _unidades(texto)
    if len(unidades) <= 1:
        return SegmentacionNombre(" ".join(unidades), "", orden, ConfianzaSegmentacion.BAJA)

    cantidad_apellidos = 2 if len(unidades) >= 3 else 1
    if orden == OrdenNombre.APELLIDOS_PRIMERO:
        unidades_apellidos, unidades_nombres = unidades[:cantidad_apellidos], unidades[cantidad_apellidos:]
    else:
        unidades_nombres, unidades_apellidos = unidades[:-cantidad_apellidos], unidades[-cantidad_apellidos:]
    return SegmentacionNombre(
        nombres=" ".join(unidades_nombres),
        apellidos=" ".join(unidades_apellidos),
        orden=orden,
        confianza=_confianza(len(unidades), hubo_particulas),
    )
