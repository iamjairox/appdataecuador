"""Tests: cargar_rule_engine_foro -- Modulo 8."""

from __future__ import annotations

import pytest

from govdata.config.rule_engine_foro import cargar_rule_engine_foro
from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError


class TestCargarRuleEngineForo:
    def test_carga_los_yaml_reales_del_proyecto(self) -> None:
        reglas = cargar_rule_engine_foro()
        assert reglas.campos.campo_por_etiqueta["NO REGISTRO"] == "registro"
        assert reglas.cache.dias_vigencia == 7
        assert reglas.circuito.umbral_fallos == 5
        assert reglas.circuito.segundos_enfriamiento == 60.0

    def test_directorio_inexistente_lanza_error(self, tmp_path) -> None:
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_foro(tmp_path / "no_existe")

    def test_yaml_sin_clave_campos_lanza_error(self, tmp_path) -> None:
        (tmp_path / "campos_foro.yaml").write_text("otra_clave: {}\n", encoding="utf-8")
        (tmp_path / "cache_foro.yaml").write_text("dias_vigencia: 7\n", encoding="utf-8")
        (tmp_path / "circuito_foro.yaml").write_text("umbral_fallos: 5\nsegundos_enfriamiento: 60.0\n", encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_foro(tmp_path)
