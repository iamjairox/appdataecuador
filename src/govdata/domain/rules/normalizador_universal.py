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
    convencion de origen es "Nombres Apellidos" o "Apellidos Nombres"
    (ambiguo sin mas contexto; ver decision documentada en el informe del
    modulo). Queda como mejora futura reemplazarla por un segmentador de
    nombres mas inteligente.
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
        for encabezado, campo in mapeo.items():
            valor = (fila_cruda.get(encabezado) or "").strip()
            if valor:
                valores.setdefault(campo, valor)

        nombres = valores.get("nombres", "")
        apellidos = valores.get("apellidos", "")
        if not nombres and not apellidos and _CAMPO_NOMBRE_COMPLETO in valores:
            nombres, apellidos = dividir_nombre_completo(valores[_CAMPO_NOMBRE_COMPLETO])

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
            )
        )
    return filas_normalizadas
