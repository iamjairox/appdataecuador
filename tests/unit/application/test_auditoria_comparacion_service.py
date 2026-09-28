"""Tests: AuditoriaComparacionService (Submodulo 5.9)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.services.auditoria_comparacion_service import AuditoriaComparacionService
from tests.unit.application.fakes_modulo5 import FakeAuditoriaComparacionRepository


def _servicio(repo: FakeAuditoriaComparacionRepository, ahora: datetime) -> AuditoriaComparacionService:
    return AuditoriaComparacionService(repo, ahora_provider=lambda: ahora)


def test_iniciar_registra_auditoria() -> None:
    repo = FakeAuditoriaComparacionRepository()
    inicio = datetime(2026, 7, 1, 10, 0, 0, tzinfo=UTC)
    servicio = _servicio(repo, inicio)
    auditoria = servicio.iniciar(entidad_id=1, documento_id=10, version_documento=2, ejecutado_por="cli")
    assert auditoria.iniciado_en == inicio
    assert auditoria.ejecutado_por == "cli"
    assert len(repo.guardadas) == 1


def test_finalizar_calcula_duracion_y_persiste_la_misma_fila() -> None:
    repo = FakeAuditoriaComparacionRepository()
    inicio = datetime(2026, 7, 1, 10, 0, 0, tzinfo=UTC)
    servicio = _servicio(repo, inicio)
    auditoria = servicio.iniciar(1, 10, 1)

    fin = datetime(2026, 7, 1, 10, 0, 10, tzinfo=UTC)
    servicio2 = _servicio(repo, fin)
    finalizada = servicio2.finalizar(auditoria, cambios_detectados=5)

    assert finalizada.duracion_segundos == 10.0
    assert finalizada.cambios_detectados == 5
    assert len(repo.guardadas) == 1  # actualiza, no duplica


def test_marcar_error_agrega_mensaje() -> None:
    repo = FakeAuditoriaComparacionRepository()
    inicio = datetime(2026, 7, 1, 10, 0, 0, tzinfo=UTC)
    servicio = _servicio(repo, inicio)
    auditoria = servicio.iniciar(1, 10, 1)

    servicio.marcar_error(auditoria, "fallo de red")
    assert "fallo de red" in auditoria.errores
    assert len(repo.guardadas) == 1
