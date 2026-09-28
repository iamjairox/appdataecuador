"""Regla de dominio: Normalizador del Foro -- Submodulo 8.3.

    "No. Registro" -> "registro"
    "Provincia"     -> "provincia"
    "Estado"        -> "estado"

Dos normalizaciones distintas, igual que en Modulo 7:

    1. Nombres de CAMPO (etiquetas del HTML): "No. Registro", "N°
       Registro", "Registro" son variantes reales de lo mismo -- viven en
       YAML (Submodulo 8.3, "nunca hardcodear"), el catalogo se busca
       SIEMPRE sobre la etiqueta ya normalizada.
    2. Valores de campo (provincia, estado, nombre): normalizacion basica
       (`normalizar_texto`) alcanza para la mayoria; `estado` ademas se
       interpreta a un Value Object cerrado (`interpretar_estado_foro`),
       igual que `interpretar_estado_registro` en Modulo 7.
"""

from __future__ import annotations

from dataclasses import replace

from govdata.application.dto.registro_foro_dto import RegistroForoDTO
from govdata.domain.rules.normalizacion import normalizar_texto
from govdata.domain.rules.reglas_foro import CatalogoCamposForo, RuleEngineForo
from govdata.domain.value_objects.estado_registro_foro import EstadoRegistroForo

_ESTADOS_CONOCIDOS = {
    "VIGENTE": EstadoRegistroForo.VIGENTE,
    "ACTIVO": EstadoRegistroForo.VIGENTE,
    "HABILITADO": EstadoRegistroForo.VIGENTE,
    "SUSPENDIDO": EstadoRegistroForo.SUSPENDIDO,
    "ANULADO": EstadoRegistroForo.ANULADO,
    "ANULADA": EstadoRegistroForo.ANULADO,
}


def interpretar_estado_foro(texto: str | None) -> EstadoRegistroForo:
    """Traduce el texto libre de `estado` (ya normalizado por el Foro o
    por el catalogo) al Value Object -- cualquier valor no reconocido cae
    en `DESCONOCIDO`, nunca falla el pipeline por un estado nuevo que el
    Foro empiece a reportar."""
    if not texto:
        return EstadoRegistroForo.DESCONOCIDO
    return _ESTADOS_CONOCIDOS.get(normalizar_texto(texto), EstadoRegistroForo.DESCONOCIDO)


def normalizar_etiqueta_campo(etiqueta: str, catalogo: CatalogoCamposForo) -> str | None:
    """Traduce una etiqueta cruda del HTML (ej. "No. Registro:") al
    nombre canonico del campo (ej. "registro"). Retorna `None` si la
    etiqueta no esta en el catalogo -- el parser HTML (8.4) simplemente
    ignora esa fila en vez de fallar toda la extraccion."""
    clave = normalizar_texto(etiqueta.rstrip(":"))
    return catalogo.campo_por_etiqueta.get(clave)


def normalizar_registro_foro(dto: RegistroForoDTO, reglas: RuleEngineForo) -> RegistroForoDTO:
    """Retorna una copia normalizada de `dto`. `registro` y `cedula`
    NUNCA se normalizan agresivamente (mas alla de recortar espacios) --
    son identificadores oficiales, no texto libre; alterarlos rompería el
    emparejamiento de registros entre consultas (Submodulo 8.5), mismo
    criterio que `numero_registro` en `normalizador_academico.py`
    (Modulo 7)."""
    return replace(
        dto,
        nombre_completo=normalizar_texto(dto.nombre_completo) if dto.nombre_completo else dto.nombre_completo,
        provincia=normalizar_texto(dto.provincia) if dto.provincia else dto.provincia,
        estado=normalizar_texto(dto.estado) if dto.estado else dto.estado,
        registro=dto.registro.strip() if dto.registro else dto.registro,
        cedula=dto.cedula.strip() if dto.cedula else dto.cedula,
    )
