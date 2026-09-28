"""Regla de dominio: Normalizador Universal -- Submodulo 4.2.

Los documentos de distintas entidades nunca usan los mismos encabezados
de columna para lo mismo ("Nombre Completo", "Servidor", "Funcionario",
"Apellidos y Nombres"...). Esta regla mapea encabezados arbitrarios a los
campos canonicos (`nombres`, `apellidos`, `cargo`, `dependencia`,
`correo`, `telefono`) usando un diccionario de sinonimos CARGADO desde
afuera (`RuleEngine`, YAML) -- nunca hardcodeado aqui -- y matching
difuso (RapidFuzz) para tolerar variaciones menores de redaccion.

Pura: no lee archivos ni conoce YAML. Recibe el diccionario ya cargado
como datos (`dict[str, list[str]]`).
"""

from __future__ import annotations

from rapidfuzz import fuzz

from govdata.application.dto.fila_extraida_dto import FilaExtraidaDTO
from govdata.application.dto.tabla_extraida_dto import TablaExtraidaDTO
from govdata.domain.rules.normalizacion import normalizar_texto
from govdata.domain.rules.reglas_configurables import ReglasNormalizacion
from govdata.domain.rules.segmentador_nombre import (
    detectar_orden_por_encabezado,
    segmentar_nombre_completo,
)

UMBRAL_MATCH_ENCABEZADO_DEFECTO = 80.0

_CAMPO_NOMBRE_COMPLETO = "nombre_completo"


def _mapear_encabezados(
    encabezados: tuple[str, ...], sinonimos_por_campo: dict[str, list[str]], umbral: float
) -> dict[str, str]:
    """`{encabezado_original: campo_canonico}` para los que superan el umbral."""
    sinonimos_normalizados = {
        campo: [normalizar_texto(s) for s in sinonimos] for campo, sinonimos in sinonimos_por_campo.items()
    }

    mapeo: dict[str, str] = {}
    for encabezado in encabezados:
        encabezado_normalizado = normalizar_texto(encabezado)
        if not encabezado_normalizado:
            continue
        mejor_campo: str | None = None
        mejor_score = 0.0
        for campo, sinonimos in sinonimos_normalizados.items():
            for sinonimo in sinonimos:
                score = fuzz.token_sort_ratio(encabezado_normalizado, sinonimo)
                if score > mejor_score:
                    mejor_score, mejor_campo = score, campo
        if mejor_campo is not None and mejor_score >= umbral:
            mapeo[encabezado] = mejor_campo
    return mapeo


def contar_encabezados_reconocidos(celdas: tuple[str, ...], reglas: ReglasNormalizacion) -> int:
    """Cuantas celdas de una fila se reconocen como encabezado canonico, con
    el MISMO mapeo difuso que `normalizar_tabla` -- base de la deteccion de
    la fila de encabezado (`detector_encabezado.py`), para que no exista
    una segunda lista de sinonimos paralela a la del YAML."""
    return len(_mapear_encabezados(celdas, reglas.sinonimos_por_campo, UMBRAL_MATCH_ENCABEZADO_DEFECTO))


def dividir_nombre_completo(nombre_completo: str) -> tuple[str, str]:
    """Heuristica de particion de un nombre combinado en (nombres, apellidos).

    Divide la lista de palabras a la mitad -- NO intenta adivinar si la
    convencion de origen es "Nombres Apellidos" o "Apellidos Nombres".
    `normalizar_tabla` ya no la usa directamente: delega en
    `segmentador_nombre.segmentar_nombre_completo`, que deduce el orden del
    encabezado y solo recurre a esta division (con confianza BAJA) cuando
    el orden es desconocido.
    """
    palabras = nombre_completo.split()
    if len(palabras) <= 1:
        return nombre_completo, ""
    mitad = (len(palabras) + 1) // 2  # la palabra impar sobrante va a "nombres"
    return " ".join(palabras[:mitad]), " ".join(palabras[mitad:])


def normalizar_tabla(tabla: TablaExtraidaDTO, reglas: ReglasNormalizacion) -> list[FilaExtraidaDTO]:
    """Convierte una `TablaExtraidaDTO` cruda en filas con campos canonicos.

    Filas sin ningun dato de nombre se descartan (no hay a quien
    persistir). Cualquier otro campo ausente ("Columnas inexistentes")
    simplemente queda vacio/`None` -- nunca lanza excepcion por fila.
    """
    mapeo = _mapear_encabezados(tabla.encabezados, reglas.sinonimos_por_campo, UMBRAL_MATCH_ENCABEZADO_DEFECTO)

    filas_normalizadas: list[FilaExtraidaDTO] = []
    for fila_cruda in tabla.filas:
        valores: dict[str, str] = {}
        encabezado_de: dict[str, str] = {}
        for encabezado, campo in mapeo.items():
            valor = (fila_cruda.get(encabezado) or "").strip()
            if valor and campo not in valores:
                valores[campo] = valor
                encabezado_de[campo] = encabezado

        nombres = valores.get("nombres", "")
        apellidos = valores.get("apellidos", "")
        nombre_completo_original: str | None = None
        orden: str | None = None
        confianza: str | None = None
        if not nombres and not apellidos and _CAMPO_NOMBRE_COMPLETO in valores:
            nombre_completo_original = valores[_CAMPO_NOMBRE_COMPLETO]
            segmentacion = segmentar_nombre_completo(
                nombre_completo_original, detectar_orden_por_encabezado(encabezado_de[_CAMPO_NOMBRE_COMPLETO])
            )
            nombres, apellidos = segmentacion.nombres, segmentacion.apellidos
            orden, confianza = segmentacion.orden.value, segmentacion.confianza.value

        if not nombres and not apellidos:
            continue

        filas_normalizadas.append(
            FilaExtraidaDTO(
                nombres=nombres,
                apellidos=apellidos,
                cargo=valores.get("cargo", ""),
                dependencia=valores.get("dependencia", ""),
                correo=valores.get("correo"),
                telefono=valores.get("telefono"),
                nombre_completo_original=nombre_completo_original,
                orden_nombre=orden,
                confianza_segmentacion=confianza,
                ciudad=valores.get("ciudad"),
            )
        )
    return filas_normalizadas
