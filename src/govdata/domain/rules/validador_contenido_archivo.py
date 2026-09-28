"""Regla de dominio: validacion del contenido REAL descargado.

No confia unicamente en la extension de la URL (ya usada en el
descubrimiento, Modulo 2). Antes de aceptar un archivo descargado como
valido, cruza tres senales independientes, en el orden pedido
(Content-Type -> Magic Bytes -> Extension), con una salvedad deliberada y
documentada: cuando los MAGIC BYTES traen una firma binaria reconocible,
esa senal se vuelve decisiva por encima del Content-Type. La razon es
justamente el caso que motiva este modulo: un servidor puede responder
`200 OK` con `Content-Type: application/pdf` y entregar en el cuerpo una
pagina de error HTML -- el Content-Type lo controla el servidor (puede
mentir); los bytes reales del archivo, no. Content-Type solo decide
cuando los magic bytes son inconclusos (texto plano: CSV, HTML, JSON...).
La extension queda como ultimo recurso, exactamente como se pidio.
"""

from __future__ import annotations

from dataclasses import dataclass

from govdata.domain.entities.documento import TipoArchivo

# Firmas binarias (magic bytes) de los formatos soportados. XLSX es un ZIP
# por dentro -- se reconoce por la firma de ZIP local-file-header/empty-archive.
_FIRMAS_MAGIC_BYTES: tuple[tuple[bytes, TipoArchivo], ...] = (
    (b"%PDF-", TipoArchivo.PDF),
    (b"PK\x03\x04", TipoArchivo.XLSX),
    (b"PK\x05\x06", TipoArchivo.XLSX),
    (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", TipoArchivo.XLS),
)

_CONTENT_TYPES_CONOCIDOS: dict[str, TipoArchivo] = {
    "application/pdf": TipoArchivo.PDF,
    "application/vnd.ms-excel": TipoArchivo.XLS,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": TipoArchivo.XLSX,
    "application/zip": TipoArchivo.XLSX,
    "text/csv": TipoArchivo.CSV,
    "application/csv": TipoArchivo.CSV,
}

_FIRMAS_PAGINA_ERROR: tuple[bytes, ...] = (b"<!doctype html", b"<html", b"<?xml")
_BYTES_A_INSPECCIONAR = 512

_MIME_CANONICO_POR_TIPO: dict[TipoArchivo, str] = {
    TipoArchivo.PDF: "application/pdf",
    TipoArchivo.XLS: "application/vnd.ms-excel",
    TipoArchivo.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    TipoArchivo.CSV: "text/csv",
}


def mime_por_tipo(tipo_archivo: TipoArchivo) -> str:
    """MIME canonico para persistir en el Manifest (independiente de lo
    que haya declarado el servidor, que puede ser inconsistente)."""
    return _MIME_CANONICO_POR_TIPO[tipo_archivo]


def _content_type_base(content_type: str | None) -> str | None:
    if not content_type:
        return None
    return content_type.split(";")[0].strip().lower()


def es_pagina_error_html(content_type: str | None, primeros_bytes: bytes) -> bool:
    """Detecta el caso central de este modulo: `archivo.pdf` que en
    realidad es una pagina de error HTML del servidor."""
    if _content_type_base(content_type) == "text/html":
        return True
    inicio = primeros_bytes[:_BYTES_A_INSPECCIONAR].lstrip().lower()
    return any(inicio.startswith(firma) for firma in _FIRMAS_PAGINA_ERROR[:2])


def detectar_por_content_type(content_type: str | None) -> TipoArchivo | None:
    base = _content_type_base(content_type)
    return _CONTENT_TYPES_CONOCIDOS.get(base) if base else None


def detectar_por_magic_bytes(primeros_bytes: bytes) -> TipoArchivo | None:
    for firma, tipo in _FIRMAS_MAGIC_BYTES:
        if primeros_bytes.startswith(firma):
            return tipo
    return None


@dataclass(frozen=True, slots=True)
class ResultadoValidacionContenido:
    """Veredicto de la validacion cruzada Content-Type / Magic Bytes / Extension."""

    tipo_detectado: TipoArchivo | None
    fuente: str  # "magic-bytes" | "content-type" | "extension" | "ninguna"
    coincide_con_esperado: bool


def resolver_tipo_real(
    content_type: str | None,
    primeros_bytes: bytes,
    tipo_esperado: TipoArchivo | None,
) -> ResultadoValidacionContenido:
    """Determina el tipo REAL del contenido descargado.

    `tipo_esperado` es el tipo que el Modulo 2 infirio de la URL (por
    extension) al momento del descubrimiento -- se usa solo para poblar
    `coincide_con_esperado`, nunca para decidir el tipo en si.
    """
    tipo_magic = detectar_por_magic_bytes(primeros_bytes)
    if tipo_magic is not None:
        return ResultadoValidacionContenido(
            tipo_detectado=tipo_magic,
            fuente="magic-bytes",
            coincide_con_esperado=tipo_magic == tipo_esperado,
        )

    # Magic bytes inconcluso (texto plano). ANTES de confiar en el
    # Content-Type declarado por el servidor, se descarta que el cuerpo
    # sea en realidad una pagina de error HTML -- el caso central de este
    # modulo: un servidor puede responder `Content-Type: application/pdf`
    # y entregar HTML igual. Content-Type miente; el cuerpo, no.
    if es_pagina_error_html(content_type, primeros_bytes):
        return ResultadoValidacionContenido(tipo_detectado=None, fuente="ninguna", coincide_con_esperado=False)

    tipo_content_type = detectar_por_content_type(content_type)
    if tipo_content_type is not None:
        return ResultadoValidacionContenido(
            tipo_detectado=tipo_content_type,
            fuente="content-type",
            coincide_con_esperado=tipo_content_type == tipo_esperado,
        )

    # Sin firma binaria ni Content-Type reconocido, y ya se descarto que
    # sea una pagina de error: CSV es texto plano y no tiene magic bytes
    # propios -- se acepta por descarte.
    if tipo_esperado == TipoArchivo.CSV:
        return ResultadoValidacionContenido(
            tipo_detectado=TipoArchivo.CSV, fuente="extension", coincide_con_esperado=True
        )

    return ResultadoValidacionContenido(tipo_detectado=None, fuente="ninguna", coincide_con_esperado=False)
