"""Adaptador: SqlAlchemyDocumentoRepository."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy import CursorResult, select, update
from sqlalchemy.orm import Session

from govdata.application.ports.documento_repository_port import DocumentoRepositoryPort
from govdata.domain.entities.documento import DocumentoTransparencia, EstadoDocumento
from govdata.infrastructure.persistence.postgresql.mappers import documento_mapper
from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel

_ESTADOS_RECLAMABLES = (EstadoDocumento.DESCUBIERTO, EstadoDocumento.ERROR)


class SqlAlchemyDocumentoRepository(DocumentoRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def guardar_o_actualizar(self, documento: DocumentoTransparencia) -> DocumentoTransparencia:
        modelo_existente = (
            self._session.execute(
                select(DocumentoModel).where(DocumentoModel.publicacion_id == documento.publicacion_id)
            )
            .scalars()
            .first()
        )
        modelo = documento_mapper.a_modelo(documento, modelo_existente)
        if modelo_existente is None:
            self._session.add(modelo)
        self._session.flush()
        return documento_mapper.a_dominio(modelo)

    def buscar_por_hash(self, hash_sha256: str) -> DocumentoTransparencia | None:
        modelo = (
            self._session.execute(select(DocumentoModel).where(DocumentoModel.hash_sha256 == hash_sha256))
            .scalars()
            .first()
        )
        return documento_mapper.a_dominio(modelo) if modelo else None

    def buscar_por_publicacion(self, publicacion_id: int) -> DocumentoTransparencia | None:
        modelo = (
            self._session.execute(
                select(DocumentoModel).where(DocumentoModel.publicacion_id == publicacion_id)
            )
            .scalars()
            .first()
        )
        return documento_mapper.a_dominio(modelo) if modelo else None

    def buscar_por_id(self, documento_id: int) -> DocumentoTransparencia | None:
        modelo = self._session.get(DocumentoModel, documento_id)
        return documento_mapper.a_dominio(modelo) if modelo else None

    def reclamar_para_descarga(self, documento_id: int) -> bool:
        resultado = cast(
            CursorResult,
            self._session.execute(
                update(DocumentoModel)
                .where(
                    DocumentoModel.id == documento_id,
                    DocumentoModel.estado.in_(_ESTADOS_RECLAMABLES),
                )
                .values(estado=EstadoDocumento.DESCARGANDO)
            ),
        )
        self._session.flush()
        return resultado.rowcount == 1

    def listar_pendientes(self, limite: int) -> list[DocumentoTransparencia]:
        modelos = (
            self._session.execute(
                select(DocumentoModel)
                .where(DocumentoModel.estado.in_(_ESTADOS_RECLAMABLES))
                .order_by(DocumentoModel.descubierto_en.asc())
                .limit(limite)
            )
            .scalars()
            .all()
        )
        return [documento_mapper.a_dominio(m) for m in modelos]

    def liberar_estancados(self, minutos_limite: int) -> int:
        limite = datetime.now(UTC) - timedelta(minutes=minutos_limite)
        resultado = cast(
            CursorResult,
            self._session.execute(
                update(DocumentoModel)
                .where(
                    DocumentoModel.estado == EstadoDocumento.DESCARGANDO,
                    DocumentoModel.actualizado_en < limite,
                )
                .values(estado=EstadoDocumento.DESCUBIERTO)
            ),
        )
        self._session.flush()
        return resultado.rowcount
