"""Tests: AuditoriaEtapa -- Submodulos 9.10/9.15."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from govdata.domain.entities.auditoria_etapa import AuditoriaEtapa
from govdata.domain.exceptions.domain_exceptions import AuditoriaEtapaInvalidaError
from govdata.domain.value_objects.estado_paso import EstadoPaso
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestAuditoriaEtapa:
    def test_omitido_requiere_razon(self) -> None:
        with pytest.raises(AuditoriaEtapaInvalidaError):
            AuditoriaEtapa(
                trabajo_orquestador_id="x", tipo_paso=TipoPasoPipeline.SENESCYT, estado_paso=EstadoPaso.OMITIDO,
                iniciado_en=_AHORA,
            )

    def test_omitido_con_razon_es_valido(self) -> None:
        etapa = AuditoriaEtapa(
            trabajo_orquestador_id="x", tipo_paso=TipoPasoPipeline.SENESCYT, estado_paso=EstadoPaso.OMITIDO,
            iniciado_en=_AHORA, razon_omision="cache_vigente",
        )
        assert etapa.razon_omision == "cache_vigente"

    def test_finalizado_antes_de_iniciado_falla(self) -> None:
        with pytest.raises(AuditoriaEtapaInvalidaError):
            AuditoriaEtapa(
                trabajo_orquestador_id="x", tipo_paso=TipoPasoPipeline.FORO, estado_paso=EstadoPaso.EJECUTADO,
                iniciado_en=_AHORA, finalizado_en=_AHORA - timedelta(seconds=1),
            )

    def test_duracion_segundos_calculada(self) -> None:
        etapa = AuditoriaEtapa(
            trabajo_orquestador_id="x", tipo_paso=TipoPasoPipeline.FORO, estado_paso=EstadoPaso.EJECUTADO,
            iniciado_en=_AHORA, finalizado_en=_AHORA + timedelta(seconds=5),
        )
        assert etapa.duracion_segundos == 5.0

    def test_duracion_segundos_none_sin_finalizar(self) -> None:
        etapa = AuditoriaEtapa(
            trabajo_orquestador_id="x", tipo_paso=TipoPasoPipeline.FORO, estado_paso=EstadoPaso.EJECUTADO,
            iniciado_en=_AHORA,
        )
        assert etapa.duracion_segundos is None
