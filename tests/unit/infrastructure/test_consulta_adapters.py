"""Tests unitarios: los tres adaptadores que implementan los puertos de
consulta del Modulo 4 (`DescubrimientoPort`, `DescargaPort`,
`ExtraccionPort`), con fakes para los workers/casos de uso/storage que
envuelven -- verifica SOLO la logica de traduccion propia del adaptador
(nunca-lanza -> lanza, resolucion de ruta local, etc.), no la logica ya
cubierta por los tests del Modulo 2/3 o por `ExtraerDocumentoUseCase`.
"""

from __future__ import annotations

from datetime import date

import pytest

from govdata.application.dto.resultado_descarga_dto import ResultadoDescargaDocumentoDTO
from govdata.application.dto.resultado_descubrimiento_dto import ResultadoDescubrimientoEntidadDTO
from govdata.application.dto.resultado_unificado_dto import (
    DocumentoResumenDTO,
    EntidadResumenDTO,
    ResultadoUnificadoDTO,
)
from govdata.domain.entities.documento import DocumentoTransparencia, TipoArchivo
from govdata.domain.entities.entidad import Entidad
from govdata.domain.exceptions.domain_exceptions import DescargaFallidaError, ExtraccionFallidaError
from govdata.infrastructure.consulta.documento_descarga_adapter import DocumentoDescargaAdapter
from govdata.infrastructure.consulta.documento_extraccion_adapter import DocumentoExtraccionAdapter
from govdata.infrastructure.consulta.dpe_descubrimiento_adapter import DpeDescubrimientoAdapter


def _entidad() -> Entidad:
    return Entidad(id=1, nombre="Entidad X", url_transparencia="https://x/1", portal_origen="dpe")


def _documento(ruta_almacenamiento: str | None = "file:///tmp/d.pdf") -> DocumentoTransparencia:
    return DocumentoTransparencia(
        id=10,
        publicacion_id=1,
        tipo_archivo=TipoArchivo.PDF,
        nombre_original="d.pdf",
        url_documento="https://x/d.pdf",
        ruta_almacenamiento=ruta_almacenamiento,
    )


class _FakeDpeWorker:
    def __init__(self, resultado: ResultadoDescubrimientoEntidadDTO) -> None:
        self._resultado = resultado
        self.cerrado = False

    def procesar(self, entidad: Entidad) -> ResultadoDescubrimientoEntidadDTO:
        return self._resultado

    def cerrar(self) -> None:
        self.cerrado = True


class TestDpeDescubrimientoAdapter:
    def test_delega_en_el_worker(self) -> None:
        resultado_esperado = ResultadoDescubrimientoEntidadDTO(entidad=_entidad(), publicacion=None, documento=None, exito=True)
        worker = _FakeDpeWorker(resultado_esperado)
        adaptador = DpeDescubrimientoAdapter(worker)

        resultado = adaptador.descubrir(_entidad())

        assert resultado is resultado_esperado

    def test_cerrar_delega_en_el_worker(self) -> None:
        worker = _FakeDpeWorker(ResultadoDescubrimientoEntidadDTO(entidad=_entidad(), publicacion=None, documento=None, exito=True))
        adaptador = DpeDescubrimientoAdapter(worker)
        adaptador.cerrar()
        assert worker.cerrado is True


class _FakeDescargaWorker:
    def __init__(self, resultado: ResultadoDescargaDocumentoDTO) -> None:
        self._resultado = resultado
        self.cerrado = False

    def procesar(self, documento: DocumentoTransparencia) -> ResultadoDescargaDocumentoDTO:
        return self._resultado

    def cerrar(self) -> None:
        self.cerrado = True


class TestDocumentoDescargaAdapter:
    def test_descarga_exitosa_devuelve_el_documento(self) -> None:
        documento_descargado = _documento()
        worker = _FakeDescargaWorker(ResultadoDescargaDocumentoDTO(documento=documento_descargado, exito=True))
        adaptador = DocumentoDescargaAdapter(worker)

        resultado = adaptador.descargar(_documento())

        assert resultado is documento_descargado

    def test_descarga_fallida_lanza_descarga_fallida_error(self) -> None:
        worker = _FakeDescargaWorker(ResultadoDescargaDocumentoDTO(documento=_documento(), exito=False, error="timeout"))
        adaptador = DocumentoDescargaAdapter(worker)

        with pytest.raises(DescargaFallidaError, match="timeout"):
            adaptador.descargar(_documento())

    def test_descarga_fallida_sin_mensaje_usa_mensaje_generico(self) -> None:
        worker = _FakeDescargaWorker(ResultadoDescargaDocumentoDTO(documento=_documento(), exito=False, error=None))
        adaptador = DocumentoDescargaAdapter(worker)

        with pytest.raises(DescargaFallidaError, match="10"):
            adaptador.descargar(_documento())

    def test_cerrar_delega_en_el_worker(self) -> None:
        worker = _FakeDescargaWorker(ResultadoDescargaDocumentoDTO(documento=_documento(), exito=True))
        adaptador = DocumentoDescargaAdapter(worker)
        adaptador.cerrar()
        assert worker.cerrado is True


class _FakeCasoUsoExtraccion:
    def __init__(self, resultado: ResultadoUnificadoDTO) -> None:
        self._resultado = resultado
        self.rutas_recibidas: list[str] = []

    def ejecutar(self, entidad, documento, ruta_archivo_local, mes_publicado):
        self.rutas_recibidas.append(ruta_archivo_local)
        return self._resultado


class _FakeFileStorage:
    def __init__(self, contenido: bytes) -> None:
        self._contenido = contenido
        self.claves_leidas: list[str] = []

    def guardar(self, contenido: bytes, ruta_relativa: str) -> str:
        raise NotImplementedError

    def leer(self, ruta_relativa: str) -> bytes:
        self.claves_leidas.append(ruta_relativa)
        return self._contenido

    def existe(self, ruta_relativa: str) -> bool:
        return True


def _resultado_unificado() -> ResultadoUnificadoDTO:
    return ResultadoUnificadoDTO(
        entidad=EntidadResumenDTO(id=1, nombre="Entidad X", portal_origen="dpe"),
        documento=DocumentoResumenDTO(id=10, tipo_archivo="pdf", mes_publicado=date(2026, 6, 1), hash_sha256="a" * 64, version=1, url="x"),
        funcionarios=[],
    )


class TestDocumentoExtraccionAdapter:
    def test_ruta_file_se_usa_directamente_sin_tocar_storage(self) -> None:
        caso_uso = _FakeCasoUsoExtraccion(_resultado_unificado())
        storage = _FakeFileStorage(b"no deberia leerse")
        adaptador = DocumentoExtraccionAdapter(caso_uso, storage)

        resultado = adaptador.extraer(_entidad(), _documento("file:///tmp/carpeta/d.pdf"), date(2026, 6, 1))

        assert resultado is caso_uso._resultado
        assert caso_uso.rutas_recibidas == ["/tmp/carpeta/d.pdf"]
        assert storage.claves_leidas == []

    def test_ruta_minio_se_descarga_a_temporal_y_se_limpia(self) -> None:
        caso_uso = _FakeCasoUsoExtraccion(_resultado_unificado())
        storage = _FakeFileStorage(b"contenido binario del pdf")
        adaptador = DocumentoExtraccionAdapter(caso_uso, storage)

        import os

        adaptador.extraer(_entidad(), _documento("minio://bucket/ab/hash123.pdf"), date(2026, 6, 1))

        assert storage.claves_leidas == ["ab/hash123.pdf"]
        assert len(caso_uso.rutas_recibidas) == 1
        # El archivo temporal se elimina despues de usarse.
        assert not os.path.exists(caso_uso.rutas_recibidas[0])

    def test_sin_ruta_almacenamiento_lanza_extraccion_fallida(self) -> None:
        caso_uso = _FakeCasoUsoExtraccion(_resultado_unificado())
        adaptador = DocumentoExtraccionAdapter(caso_uso, _FakeFileStorage(b""))

        with pytest.raises(ExtraccionFallidaError):
            adaptador.extraer(_entidad(), _documento(None), date(2026, 6, 1))
