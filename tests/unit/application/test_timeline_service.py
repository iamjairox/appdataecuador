"""Tests: TimelineService (Submodulo 5.13)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.resultado_unificado_dto import EntidadResumenDTO
from govdata.application.services.timeline_service import TimelineService
from govdata.domain.entities.alerta import Alerta, TipoAlerta
from govdata.domain.entities.auditoria_comparacion import AuditoriaComparacion
from govdata.domain.entities.documento import DocumentoTransparencia, EstadoDocumento, TipoArchivo
from govdata.domain.entities.verificacion import Verificacion
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from tests.unit.application.fakes import FakeDocumentoRepository
from tests.unit.application.fakes_modulo5 import (
    FakeAlertaRepository,
    FakeAuditoriaComparacionRepository,
    FakeVerificacionRepository,
)


def _servicio(verificacion_repo, alerta_repo, auditoria_repo, documento_repo) -> TimelineService:
    return TimelineService(verificacion_repo, alerta_repo, auditoria_repo, documento_repo)


def test_timeline_vacio_sin_verificaciones() -> None:
    servicio = _servicio(
        FakeVerificacionRepository(), FakeAlertaRepository(), FakeAuditoriaComparacionRepository(), FakeDocumentoRepository()
    )
    timeline = servicio.construir(EntidadResumenDTO(id=1, nombre="Entidad X", portal_origen="dpe"))
    assert timeline.puntos == []


def test_timeline_con_puntos_enriquecidos_de_alertas_y_cambios() -> None:
    verificacion_repo = FakeVerificacionRepository()
    alerta_repo = FakeAlertaRepository()
    auditoria_repo = FakeAuditoriaComparacionRepository()
    documento_repo = FakeDocumentoRepository()

    documento = documento_repo.guardar_o_actualizar(
        DocumentoTransparencia(
            id=1, publicacion_id=1, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf",
            url_documento="https://x/d.pdf", estado=EstadoDocumento.DESCARGADO,
            hash_sha256="a" * 64, tamano_bytes=10, ruta_almacenamiento="file:///a", version=2,
        )
    )
    verificacion_repo.registrar(
        Verificacion(
            entidad_id=1, hubo_cambio=True, motivo="cambios_detectados",
            verificado_en=datetime(2026, 7, 1, tzinfo=UTC), documento_id=documento.id,
        )
    )
    alerta_repo.guardar(
        Alerta(
            entidad_id=1, tipo=TipoAlerta.CAMBIO_CARGO, prioridad=NivelCriticidad.MEDIO,
            descripcion="x", detectado_en=datetime.now(UTC), documento_id=documento.id,
        )
    )
    auditoria_repo.registrar(
        AuditoriaComparacion(
            entidad_id=1, documento_id=documento.id, version_documento=2, ejecutado_por="sistema",
            iniciado_en=datetime.now(UTC), cambios_detectados=3,
        )
    )

    servicio = _servicio(verificacion_repo, alerta_repo, auditoria_repo, documento_repo)
    timeline = servicio.construir(EntidadResumenDTO(id=1, nombre="Entidad X", portal_origen="dpe"))

    assert len(timeline.puntos) == 1
    punto = timeline.puntos[0]
    assert punto.hubo_cambio is True
    assert punto.cantidad_alertas == 1
    assert punto.cantidad_cambios == 3
    assert punto.version_documento == 2


def test_punto_sin_documento_no_consulta_alertas_ni_auditoria() -> None:
    verificacion_repo = FakeVerificacionRepository()
    verificacion_repo.registrar(
        Verificacion(entidad_id=1, hubo_cambio=False, motivo="sin_publicacion", verificado_en=datetime.now(UTC), documento_id=None)
    )
    servicio = _servicio(
        verificacion_repo, FakeAlertaRepository(), FakeAuditoriaComparacionRepository(), FakeDocumentoRepository()
    )
    timeline = servicio.construir(EntidadResumenDTO(id=1, nombre="Entidad X", portal_origen="dpe"))
    assert timeline.puntos[0].cantidad_alertas == 0
    assert timeline.puntos[0].version_documento is None
