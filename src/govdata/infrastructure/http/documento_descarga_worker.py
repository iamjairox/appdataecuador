"""Adaptador: DocumentoDescargaWorker.

Implementacion de `DescargaWorkerPort`. Posee, por hilo, una
`RequestsHttpFetcherAdapter` propia (envuelve una `requests.Session` --
no segura para compartir entre hilos) y abre una sesion de base de datos
NUEVA por documento (Unit of Work por documento: un fallo a mitad de
camino no deja datos a medias de ESE documento, pero tampoco afecta a los
demas). El `FileStoragePort` SI se comparte entre hilos -- los adaptadores
de storage (disco local, MinIO) son seguros para escritura concurrente en
claves distintas (y las claves son content-addressable, ver
`generador_ruta_almacenamiento`).
"""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from govdata.application.dto.resultado_descarga_dto import ResultadoDescargaDocumentoDTO
from govdata.application.ports.descarga_worker_port import DescargaWorkerPort
from govdata.application.ports.file_storage_port import FileStoragePort
from govdata.application.use_cases.descargar_documento_use_case import DescargarDocumentoUseCase
from govdata.config.logging_config import get_logger
from govdata.domain.entities.documento import DocumentoTransparencia
from govdata.domain.exceptions.domain_exceptions import (
    DocumentoYaEnProcesoError,
    GovDataError,
    PresupuestoReintentosAgotadoError,
)
from govdata.infrastructure.http.requests_http_fetcher_adapter import RequestsHttpFetcherAdapter
from govdata.infrastructure.persistence.postgresql.database import sesion_scope
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_descarga_repository import (
    SqlAlchemyDescargaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_documento_repository import (
    SqlAlchemyDocumentoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_manifest_repository import (
    SqlAlchemyManifestRepository,
)

logger = get_logger(__name__)

_ERRORES_OMITIBLES = (DocumentoYaEnProcesoError, PresupuestoReintentosAgotadoError)


class DocumentoDescargaWorker(DescargaWorkerPort):
    """Worker de descarga: una sesion HTTP reutilizada, N documentos."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        storage: FileStoragePort,
        timeout_segundos: float,
        max_reintentos: int,
        backoff_base_segundos: float,
        tamano_maximo_bytes: int | None,
    ) -> None:
        self._session_factory = session_factory
        self._storage = storage
        self._max_reintentos = max_reintentos
        self._http_fetcher = RequestsHttpFetcherAdapter(
            timeout_segundos=timeout_segundos,
            max_reintentos=max_reintentos,
            backoff_base_segundos=backoff_base_segundos,
            tamano_maximo_bytes=tamano_maximo_bytes,
        )

    def procesar(self, documento: DocumentoTransparencia) -> ResultadoDescargaDocumentoDTO:
        with sesion_scope(self._session_factory) as sesion:
            caso_uso = DescargarDocumentoUseCase(
                http_fetcher=self._http_fetcher,
                storage=self._storage,
                documento_repository=SqlAlchemyDocumentoRepository(sesion),
                descarga_repository=SqlAlchemyDescargaRepository(sesion),
                manifest_repository=SqlAlchemyManifestRepository(sesion),
                max_reintentos=self._max_reintentos,
            )
            try:
                documento_actualizado = caso_uso.ejecutar(documento)
            except _ERRORES_OMITIBLES as exc:
                logger.info("documento_omitido", documento_id=documento.id, motivo=str(exc))
                return ResultadoDescargaDocumentoDTO(
                    documento=documento, exito=False, omitido=True, error=str(exc)
                )
            except GovDataError as exc:
                return ResultadoDescargaDocumentoDTO(documento=documento, exito=False, error=str(exc))

            return ResultadoDescargaDocumentoDTO(documento=documento_actualizado, exito=True)

    def cerrar(self) -> None:
        self._http_fetcher.cerrar()
