"""Tests: cargar_rule_engine_orquestador -- Modulo 9."""

from __future__ import annotations

import pytest

from govdata.config.rule_engine_orquestador import cargar_rule_engine_orquestador
from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError


class TestCargarRuleEngineOrquestador:
    def test_carga_los_yaml_reales_del_proyecto(self) -> None:
        reglas = cargar_rule_engine_orquestador()
        assert reglas.prioridad.umbral_muy_alta == 80.0
        assert reglas.cola.politica_defecto == "consulta_rapida"
        assert sorted(reglas.politicas.politicas_por_nombre) == [
            "actualizacion_completa", "consulta_rapida", "masiva_nocturna", "solo_cambios",
        ]

    def test_politica_actualizacion_completa_fuerza_actualizacion(self) -> None:
        reglas = cargar_rule_engine_orquestador()
        politica = reglas.politicas.obtener("actualizacion_completa")
        assert politica is not None
        assert politica.forzar_actualizacion is True
        assert politica.usar_cache is False

    def test_politica_masiva_nocturna_tiene_reintentos_y_prioridad(self) -> None:
        reglas = cargar_rule_engine_orquestador()
        politica = reglas.politicas.obtener("masiva_nocturna")
        assert politica is not None
        assert politica.reintentos_automaticos is True
        assert politica.prioridad_pendientes is True
        assert politica.concurrencia_maxima > 1

    def test_directorio_inexistente_lanza_error(self, tmp_path) -> None:
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_orquestador(tmp_path / "no_existe")

    def test_yaml_sin_clave_politicas_lanza_error(self, tmp_path) -> None:
        (tmp_path / "politicas_ejecucion.yaml").write_text("otra_clave: {}\n", encoding="utf-8")
        (tmp_path / "prioridades_orquestador.yaml").write_text("umbral_muy_alta: 80.0\n", encoding="utf-8")
        (tmp_path / "cola_orquestador.yaml").write_text("concurrencia_maxima_defecto: 2\n", encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_orquestador(tmp_path)

    def test_yaml_malformado_lanza_error(self, tmp_path) -> None:
        (tmp_path / "politicas_ejecucion.yaml").write_text("politicas: [no cierra\n", encoding="utf-8")
        (tmp_path / "prioridades_orquestador.yaml").write_text("umbral_muy_alta: 80.0\n", encoding="utf-8")
        (tmp_path / "cola_orquestador.yaml").write_text("concurrencia_maxima_defecto: 2\n", encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_orquestador(tmp_path)

    def test_politica_que_no_es_mapeo_lanza_error(self, tmp_path) -> None:
        (tmp_path / "politicas_ejecucion.yaml").write_text("politicas:\n  consulta_rapida: \"no es un mapeo\"\n", encoding="utf-8")
        (tmp_path / "prioridades_orquestador.yaml").write_text("umbral_muy_alta: 80.0\n", encoding="utf-8")
        (tmp_path / "cola_orquestador.yaml").write_text("concurrencia_maxima_defecto: 2\n", encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_orquestador(tmp_path)

    def test_yaml_con_raiz_que_no_es_mapeo_lanza_error(self, tmp_path) -> None:
        (tmp_path / "politicas_ejecucion.yaml").write_text("- no\n- es\n- un mapeo\n", encoding="utf-8")
        (tmp_path / "prioridades_orquestador.yaml").write_text("umbral_muy_alta: 80.0\n", encoding="utf-8")
        (tmp_path / "cola_orquestador.yaml").write_text("concurrencia_maxima_defecto: 2\n", encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_orquestador(tmp_path)
