"""Tests: VerificacionService (Submodulos 5.10/5.15)."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.services.verificacion_service import VerificacionService
from tests.unit.application.fakes_modulo5 import FakeVerificacionRepository


def test_registrar_verificacion_sin_cambio() -> None:
    repo = FakeVerificacionRepository()
    servicio = VerificacionService(repo)
    verificacion = servicio.registrar(
        entidad_id=1, hubo_cambio=False, motivo="hash_remoto_sin_cambios", verificado_en=datetime.now(UTC)
    )
    assert verificacion.hubo_cambio is False
    assert len(repo.guardadas) == 1


def test_ultima_verificacion_devuelve_la_mas_reciente() -> None:
    repo = FakeVerificacionRepository()
    servicio = VerificacionService(repo)
    servicio.registrar(1, False, "primera", datetime(2026, 6, 1, tzinfo=UTC))
    servicio.registrar(1, True, "segunda", datetime(2026, 7, 1, tzinfo=UTC))

    ultima = servicio.ultima_verificacion(1)
    assert ultima.motivo == "segunda"


def test_ultima_verificacion_sin_historial_es_none() -> None:
    repo = FakeVerificacionRepository()
    servicio = VerificacionService(repo)
    assert servicio.ultima_verificacion(999) is None
