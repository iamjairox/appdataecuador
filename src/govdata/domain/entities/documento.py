"""Entidad de dominio: DocumentoTransparencia.

Modela el ciclo de vida completo de un documento fuente como una maquina
de estados:

    DESCUBIERTO -> DESCARGANDO -> DESCARGADO
                                -> ERROR (reintentable: vuelve a DESCUBIERTO)
    DESCARGADO  -> OBSOLETO   (cuando una redescubierta detecta un
                                reemplazo, o una nueva descarga trae un
                                hash distinto -- ver `version`)

`Documento` es el PUNTERO al estado ACTUAL del archivo de una publicacion.
El HISTORIAL de cada intento de descarga vive en `Descarga` (append-only,
una fila por intento), y el registro canonico de cada version
efectivamente almacenada vive en `Manifest` (append-only, una fila por
descarga exitosa) -- ver esos modulos. Este diseno evita perder
informacion cuando el archivo publicado cambia dentro del mismo mes: el
`Documento` siempre reflexiona el ultimo estado conocido, pero nada se
sobreescribe sin dejar rastro en `Descarga`/`Manifest`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from govdata.domain.exceptions.domain_exceptions import GovDataError


class TipoArchivo(str, Enum):
    """Formatos de documento reconocidos por el Modulo de Extraccion.

    `CSV` se agrego tras verificar el portal real de la DPE: el archivo
    "Conjunto de datos" de varias entidades se publica en ese formato,
    ademas de PDF/XLS/XLSX.
    """

    PDF = "pdf"
    XLS = "xls"
    XLSX = "xlsx"
    CSV = "csv"


class EstadoDocumento(str, Enum):
    """Estado del ciclo de vida de un documento."""

    DESCUBIERTO = "descubierto"
    DESCARGANDO = "descargando"
    DESCARGADO = "descargado"
    ERROR = "error"
    OBSOLETO = "obsoleto"


class DocumentoInvalidoError(GovDataError):
    """Un DocumentoTransparencia no cumple sus invariantes."""


class TransicionEstadoInvalidaError(GovDataError):
    """Se intento una transicion de estado no permitida para un Documento."""


# Transiciones permitidas: estado_actual -> {estados_destino_validos}
_TRANSICIONES_VALIDAS: dict[EstadoDocumento, frozenset[EstadoDocumento]] = {
    EstadoDocumento.DESCUBIERTO: frozenset({EstadoDocumento.DESCARGANDO}),
    EstadoDocumento.DESCARGANDO: frozenset({EstadoDocumento.DESCARGADO, EstadoDocumento.ERROR}),
    EstadoDocumento.DESCARGADO: frozenset({EstadoDocumento.DESCARGANDO, EstadoDocumento.OBSOLETO}),
    EstadoDocumento.ERROR: frozenset({EstadoDocumento.DESCARGANDO, EstadoDocumento.OBSOLETO}),
    EstadoDocumento.OBSOLETO: frozenset(),
}


@dataclass(slots=True)
class DocumentoTransparencia:
    """Puntero al estado actual de un documento fuente."""

    publicacion_id: int
    tipo_archivo: TipoArchivo
    nombre_original: str
    url_documento: str
    id: int | None = None
    estado: EstadoDocumento = EstadoDocumento.DESCUBIERTO
    version: int = 1
    etag: str | None = None
    last_modified: str | None = None
    tamano_bytes: int | None = None
    ruta_almacenamiento: str | None = None
    hash_sha256: str | None = None
    descubierto_en: datetime | None = None
    descargado_en: datetime | None = None
    actualizado_en: datetime | None = None
    """Gestionado por la capa de persistencia (onupdate). Se usa para
    detectar documentos "estancados" en DESCARGANDO (worker caido a mitad
    de una descarga) -- ver `DocumentoRepositoryPort.liberar_estancados`."""

    def __post_init__(self) -> None:
        if not self.nombre_original or not self.nombre_original.strip():
            raise DocumentoInvalidoError("DocumentoTransparencia requiere nombre_original")
        if not self.url_documento or not self.url_documento.strip():
            raise DocumentoInvalidoError(
                f"DocumentoTransparencia '{self.nombre_original}' requiere url_documento"
            )
        if self.version < 1:
            raise DocumentoInvalidoError(f"version invalida: {self.version}")
        if self.hash_sha256 is not None and len(self.hash_sha256) != 64:
            raise DocumentoInvalidoError(f"hash_sha256 invalido: '{self.hash_sha256}'")
        if self.estado == EstadoDocumento.DESCARGADO and (
            self.ruta_almacenamiento is None or self.hash_sha256 is None or self.tamano_bytes is None
        ):
            raise DocumentoInvalidoError(
                "Un Documento en estado DESCARGADO requiere ruta_almacenamiento, "
                "hash_sha256 y tamano_bytes"
            )

    @property
    def esta_descargado(self) -> bool:
        return self.estado == EstadoDocumento.DESCARGADO

    def _transicionar(self, nuevo_estado: EstadoDocumento) -> None:
        permitidos = _TRANSICIONES_VALIDAS[self.estado]
        if nuevo_estado not in permitidos:
            raise TransicionEstadoInvalidaError(
                f"Transicion invalida: {self.estado.value} -> {nuevo_estado.value} "
                f"(documento_id={self.id})"
            )
        self.estado = nuevo_estado

    def iniciar_descarga(self) -> None:
        """DESCUBIERTO|ERROR -> DESCARGANDO. Reclama el documento para un intento."""
        self._transicionar(EstadoDocumento.DESCARGANDO)

    def completar_descarga(
        self,
        ruta_almacenamiento: str,
        hash_sha256: str,
        tamano_bytes: int,
        descargado_en: datetime,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> None:
        """DESCARGANDO -> DESCARGADO.

        Si ya existia un hash previo distinto (redescarga que trajo
        contenido nuevo), incrementa `version` -- asi se detecta que el
        archivo cambio durante el mismo mes sin depender del nombre.
        """
        if len(hash_sha256) != 64:
            raise DocumentoInvalidoError(f"hash_sha256 invalido: '{hash_sha256}'")

        if self.hash_sha256 is not None and self.hash_sha256 != hash_sha256:
            self.version += 1

        self._transicionar(EstadoDocumento.DESCARGADO)
        self.ruta_almacenamiento = ruta_almacenamiento
        self.hash_sha256 = hash_sha256
        self.tamano_bytes = tamano_bytes
        self.etag = etag
        self.last_modified = last_modified
        self.descargado_en = descargado_en

    def marcar_error(self) -> None:
        """DESCARGANDO -> ERROR. El detalle del error vive en `Descarga`."""
        self._transicionar(EstadoDocumento.ERROR)

    def reintentar(self) -> None:
        """ERROR -> DESCUBIERTO: vuelve a la cola de pendientes."""
        if self.estado != EstadoDocumento.ERROR:
            raise TransicionEstadoInvalidaError(
                f"Solo un Documento en ERROR puede reintentarse (estado actual: {self.estado.value})"
            )
        self.estado = EstadoDocumento.DESCUBIERTO

    def marcar_obsoleto(self) -> None:
        """DESCARGADO|ERROR -> OBSOLETO: reemplazado por otro documento."""
        self._transicionar(EstadoDocumento.OBSOLETO)
