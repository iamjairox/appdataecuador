"""Dobles de prueba (fakes) de los puertos del Modulo 3."""

from __future__ import annotations

from govdata.application.dto.descarga_dto import RespuestaDescargaDTO
from govdata.application.ports.descarga_repository_port import DescargaRepositoryPort
from govdata.application.ports.documento_repository_port import DocumentoRepositoryPort
from govdata.application.ports.file_storage_port import FileStoragePort
from govdata.application.ports.http_fetcher_port import HttpFetcherPort
from govdata.application.ports.manifest_repository_port import ManifestRepositoryPort
from govdata.domain.entities.descarga import Descarga
from govdata.domain.entities.documento import DocumentoTransparencia, EstadoDocumento
from govdata.domain.entities.manifest import Manifest
from govdata.domain.exceptions.domain_exceptions import GovDataError


class FakeHttpFetcherPort(HttpFetcherPort):
    def __init__(
        self, respuesta: RespuestaDescargaDTO | None = None, error_a_lanzar: GovDataError | None = None
    ) -> None:
        self._respuesta = respuesta
        self._error_a_lanzar = error_a_lanzar
        self.urls_solicitadas: list[str] = []

    def descargar(self, url: str) -> RespuestaDescargaDTO:
        self.urls_solicitadas.append(url)
        if self._error_a_lanzar:
            raise self._error_a_lanzar
        assert self._respuesta is not None
        return self._respuesta


class FakeFileStoragePort(FileStoragePort):
    def __init__(self) -> None:
        self.archivos: dict[str, bytes] = {}

    def guardar(self, contenido: bytes, ruta_relativa: str) -> str:
        self.archivos[ruta_relativa] = contenido
        return f"fake://{ruta_relativa}"

    def leer(self, ruta_relativa: str) -> bytes:
        return self.archivos[ruta_relativa]

    def existe(self, ruta_relativa: str) -> bool:
        return ruta_relativa in self.archivos


class FakeDocumentoRepositoryDescarga(DocumentoRepositoryPort):
    """Doble minimo: solo lo que `DescargarDocumentoUseCase` necesita."""

    def __init__(self, documentos: list[DocumentoTransparencia] | None = None) -> None:
        self._por_id: dict[int, DocumentoTransparencia] = {d.id: d for d in (documentos or []) if d.id}
        self.reclamos_denegados: set[int] = set()

    def guardar_o_actualizar(self, documento: DocumentoTransparencia) -> DocumentoTransparencia:
        if documento.id is not None:
            self._por_id[documento.id] = documento
        return documento

    def buscar_por_hash(self, hash_sha256: str) -> DocumentoTransparencia | None:
        return next((d for d in self._por_id.values() if d.hash_sha256 == hash_sha256), None)

    def buscar_por_publicacion(self, publicacion_id: int) -> DocumentoTransparencia | None:
        return next((d for d in self._por_id.values() if d.publicacion_id == publicacion_id), None)

    def buscar_por_id(self, documento_id: int) -> DocumentoTransparencia | None:
        return self._por_id.get(documento_id)

    def reclamar_para_descarga(self, documento_id: int) -> bool:
        if documento_id in self.reclamos_denegados:
            return False
        documento = self._por_id.get(documento_id)
        if documento is None:
            return False
        return documento.estado in (EstadoDocumento.DESCUBIERTO, EstadoDocumento.ERROR)

    def listar_pendientes(self, limite: int) -> list[DocumentoTransparencia]:
        return list(self._por_id.values())[:limite]

    def liberar_estancados(self, minutos_limite: int) -> int:
        return 0


class FakeDescargaRepository(DescargaRepositoryPort):
    def __init__(self, intentos_previos: int = 0) -> None:
        self.registradas: list[Descarga] = []
        self._intentos_previos = intentos_previos

    def registrar(self, descarga: Descarga) -> Descarga:
        descarga.id = len(self.registradas) + 1
        self.registradas.append(descarga)
        return descarga

    def listar_por_documento(self, documento_id: int) -> list[Descarga]:
        return [d for d in self.registradas if d.documento_id == documento_id]

    def contar_intentos(self, documento_id: int) -> int:
        return self._intentos_previos + len(
            [d for d in self.registradas if d.documento_id == documento_id]
        )


class FakeManifestRepository(ManifestRepositoryPort):
    def __init__(self) -> None:
        self.registrados: list[Manifest] = []

    def registrar(self, manifest: Manifest) -> Manifest:
        manifest.id = len(self.registrados) + 1
        self.registrados.append(manifest)
        return manifest

    def buscar_por_hash(self, sha256: str) -> Manifest | None:
        return next((m for m in self.registrados if m.sha256 == sha256), None)

    def listar_por_documento(self, documento_id: int) -> list[Manifest]:
        return [m for m in self.registrados if m.documento_id == documento_id]
