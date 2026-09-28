"""Tests: maquina de estados y versionado de DocumentoTransparencia,
y las entidades Descarga/Manifest."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from govdata.domain.entities.descarga import Descarga, DescargaInvalidaError, EstadoDescarga
from govdata.domain.entities.documento import (
    DocumentoInvalidoError,
    DocumentoTransparencia,
    EstadoDocumento,
    TipoArchivo,
    TransicionEstadoInvalidaError,
)
from govdata.domain.entities.manifest import Manifest, ManifestInvalidoError

_HASH_A = "a" * 64
_HASH_B = "b" * 64


def _documento(**overrides) -> DocumentoTransparencia:
    base = {
        "publicacion_id": 1,
        "tipo_archivo": TipoArchivo.PDF,
        "nombre_original": "directorio.pdf",
        "url_documento": "https://x/directorio.pdf",
    }
    base.update(overrides)
    return DocumentoTransparencia(**base)


class TestMaquinaDeEstados:
    def test_estado_inicial_es_descubierto(self) -> None:
        assert _documento().estado == EstadoDocumento.DESCUBIERTO

    def test_flujo_feliz_completo(self) -> None:
        doc = _documento()
        doc.iniciar_descarga()
        assert doc.estado == EstadoDocumento.DESCARGANDO

        doc.completar_descarga(
            ruta_almacenamiento="file:///a.pdf",
            hash_sha256=_HASH_A,
            tamano_bytes=100,
            descargado_en=datetime.now(UTC),
        )
        assert doc.estado == EstadoDocumento.DESCARGADO
        assert doc.esta_descargado is True
        assert doc.version == 1

    def test_no_se_puede_completar_sin_pasar_por_descargando(self) -> None:
        doc = _documento()
        with pytest.raises(TransicionEstadoInvalidaError):
            doc.completar_descarga(
                ruta_almacenamiento="file:///a.pdf",
                hash_sha256=_HASH_A,
                tamano_bytes=100,
                descargado_en=datetime.now(UTC),
            )

    def test_marcar_error_desde_descargando(self) -> None:
        doc = _documento()
        doc.iniciar_descarga()
        doc.marcar_error()
        assert doc.estado == EstadoDocumento.ERROR

    def test_reintentar_desde_error_vuelve_a_descubierto(self) -> None:
        doc = _documento()
        doc.iniciar_descarga()
        doc.marcar_error()
        doc.reintentar()
        assert doc.estado == EstadoDocumento.DESCUBIERTO

    def test_reintentar_fuera_de_error_lanza_error(self) -> None:
        doc = _documento()
        with pytest.raises(TransicionEstadoInvalidaError):
            doc.reintentar()

    def test_marcar_obsoleto_desde_descargado(self) -> None:
        doc = _documento()
        doc.iniciar_descarga()
        doc.completar_descarga("file:///a.pdf", _HASH_A, 100, datetime.now(UTC))
        doc.marcar_obsoleto()
        assert doc.estado == EstadoDocumento.OBSOLETO

    def test_obsoleto_es_estado_terminal(self) -> None:
        doc = _documento()
        doc.iniciar_descarga()
        doc.completar_descarga("file:///a.pdf", _HASH_A, 100, datetime.now(UTC))
        doc.marcar_obsoleto()
        with pytest.raises(TransicionEstadoInvalidaError):
            doc.iniciar_descarga()


class TestVersionado:
    def test_primera_descarga_no_incrementa_version(self) -> None:
        doc = _documento()
        doc.iniciar_descarga()
        doc.completar_descarga("file:///a.pdf", _HASH_A, 100, datetime.now(UTC))
        assert doc.version == 1

    def test_redescarga_con_mismo_hash_no_incrementa_version(self) -> None:
        doc = _documento()
        doc.iniciar_descarga()
        doc.completar_descarga("file:///a.pdf", _HASH_A, 100, datetime.now(UTC))
        doc.iniciar_descarga()
        doc.completar_descarga("file:///a.pdf", _HASH_A, 100, datetime.now(UTC))
        assert doc.version == 1

    def test_redescarga_con_hash_distinto_incrementa_version(self) -> None:
        """El caso central del requisito: el archivo publicado cambio
        durante el mismo mes -- se detecta sin depender del nombre."""
        doc = _documento()
        doc.iniciar_descarga()
        doc.completar_descarga("file:///a.pdf", _HASH_A, 100, datetime.now(UTC))
        doc.iniciar_descarga()
        doc.completar_descarga("file:///b.pdf", _HASH_B, 200, datetime.now(UTC))
        assert doc.version == 2
        assert doc.hash_sha256 == _HASH_B


class TestInvariantes:
    def test_requiere_nombre_original(self) -> None:
        with pytest.raises(DocumentoInvalidoError):
            _documento(nombre_original="")

    def test_requiere_url_documento(self) -> None:
        with pytest.raises(DocumentoInvalidoError):
            _documento(url_documento="")

    def test_hash_invalido_en_constructor(self) -> None:
        with pytest.raises(DocumentoInvalidoError):
            _documento(hash_sha256="corto")

    def test_descargado_sin_ruta_es_invalido(self) -> None:
        with pytest.raises(DocumentoInvalidoError):
            _documento(estado=EstadoDocumento.DESCARGADO, hash_sha256=_HASH_A, tamano_bytes=1)

    def test_version_menor_a_uno_es_invalida(self) -> None:
        with pytest.raises(DocumentoInvalidoError):
            _documento(version=0)


class TestDescarga:
    def _base(self, **overrides) -> dict:
        base = {
            "documento_id": 1,
            "numero_intento": 1,
            "estado": EstadoDescarga.EXITO,
            "iniciado_en": datetime(2026, 1, 1, tzinfo=UTC),
            "finalizado_en": datetime(2026, 1, 1, 0, 0, 5, tzinfo=UTC),
            "tamano_bytes": 100,
            "hash_sha256": _HASH_A,
        }
        base.update(overrides)
        return base

    def test_descarga_exitosa_valida(self) -> None:
        descarga = Descarga(**self._base())
        assert descarga.duracion_segundos == 5.0

    def test_exito_requiere_tamano_y_hash(self) -> None:
        with pytest.raises(DescargaInvalidaError):
            Descarga(**self._base(tamano_bytes=None))

    def test_fallo_requiere_mensaje_error(self) -> None:
        with pytest.raises(DescargaInvalidaError):
            Descarga(**self._base(estado=EstadoDescarga.FALLO, tamano_bytes=None, hash_sha256=None))

    def test_fallo_con_mensaje_es_valido(self) -> None:
        descarga = Descarga(
            **self._base(
                estado=EstadoDescarga.FALLO,
                tamano_bytes=None,
                hash_sha256=None,
                mensaje_error="timeout",
            )
        )
        assert descarga.estado == EstadoDescarga.FALLO

    def test_finalizado_antes_de_iniciado_es_invalido(self) -> None:
        with pytest.raises(DescargaInvalidaError):
            Descarga(
                **self._base(
                    iniciado_en=datetime(2026, 1, 1, 0, 0, 5, tzinfo=UTC),
                    finalizado_en=datetime(2026, 1, 1, tzinfo=UTC),
                )
            )

    def test_numero_intento_invalido(self) -> None:
        with pytest.raises(DescargaInvalidaError):
            Descarga(**self._base(numero_intento=0))


class TestManifest:
    def test_manifest_valido(self) -> None:
        manifest = Manifest(
            documento_id=1,
            url="https://x/a.pdf",
            sha256=_HASH_A,
            mime="application/pdf",
            bytes_totales=100,
            storage_uri="file:///a.pdf",
            fecha_descarga=datetime.now(UTC),
        )
        assert manifest.sha256 == _HASH_A

    def test_hash_invalido(self) -> None:
        with pytest.raises(ManifestInvalidoError):
            Manifest(
                documento_id=1,
                url="https://x/a.pdf",
                sha256="corto",
                mime="application/pdf",
                bytes_totales=100,
                storage_uri="file:///a.pdf",
                fecha_descarga=datetime.now(UTC),
            )

    def test_bytes_negativos(self) -> None:
        with pytest.raises(ManifestInvalidoError):
            Manifest(
                documento_id=1,
                url="https://x/a.pdf",
                sha256=_HASH_A,
                mime="application/pdf",
                bytes_totales=-1,
                storage_uri="file:///a.pdf",
                fecha_descarga=datetime.now(UTC),
            )
