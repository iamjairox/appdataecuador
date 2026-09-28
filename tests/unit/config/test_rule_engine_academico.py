"""Tests: cargador del Motor de Reglas del Modulo 7 (config/rule_engine_academico.py)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from govdata.config.rule_engine_academico import cargar_rule_engine_academico
from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError


def _escribir_yaml_validos(directorio: Path) -> None:
    (directorio / "titulos.yaml").write_text(yaml.safe_dump({"canonicos": {"LIC": "LICENCIADO"}}), encoding="utf-8")
    (directorio / "universidades.yaml").write_text(
        yaml.safe_dump({"canonicos": {"UCE": "UNIVERSIDAD CENTRAL DEL ECUADOR"}}), encoding="utf-8"
    )
    (directorio / "niveles.yaml").write_text(
        yaml.safe_dump({"canonicos": {"PREGRADO": "TERCER NIVEL"}}), encoding="utf-8"
    )
    (directorio / "cache_senescyt.yaml").write_text(yaml.safe_dump({"dias_vigencia": 30}), encoding="utf-8")


class TestCargarRuleEngineAcademico:
    def test_carga_los_yaml_del_proyecto_por_defecto(self) -> None:
        engine = cargar_rule_engine_academico()
        assert engine.titulos.canonico_por_sinonimo.get("LIC") == "LICENCIADO"
        assert engine.cache.dias_vigencia == 30

    def test_carga_directorio_alternativo(self, tmp_path: Path) -> None:
        _escribir_yaml_validos(tmp_path)
        engine = cargar_rule_engine_academico(tmp_path)
        assert engine.universidades.canonico_por_sinonimo["UCE"] == "UNIVERSIDAD CENTRAL DEL ECUADOR"
        assert engine.niveles.canonico_por_sinonimo["PREGRADO"] == "TERCER NIVEL"

    def test_archivo_faltante_falla(self, tmp_path: Path) -> None:
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_academico(tmp_path)

    def test_catalogo_sin_clave_canonicos_falla(self, tmp_path: Path) -> None:
        _escribir_yaml_validos(tmp_path)
        (tmp_path / "titulos.yaml").write_text(yaml.safe_dump({"otra_clave": {}}), encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_academico(tmp_path)

    def test_cache_dias_vigencia_por_defecto(self, tmp_path: Path) -> None:
        _escribir_yaml_validos(tmp_path)
        (tmp_path / "cache_senescyt.yaml").write_text(yaml.safe_dump({}), encoding="utf-8")
        engine = cargar_rule_engine_academico(tmp_path)
        assert engine.cache.dias_vigencia == 30

    def test_yaml_con_sintaxis_invalida_falla(self, tmp_path: Path) -> None:
        _escribir_yaml_validos(tmp_path)
        (tmp_path / "titulos.yaml").write_text("canonicos: [no cierra\n", encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_academico(tmp_path)

    def test_yaml_cuya_raiz_no_es_un_mapeo_falla(self, tmp_path: Path) -> None:
        _escribir_yaml_validos(tmp_path)
        (tmp_path / "titulos.yaml").write_text(yaml.safe_dump(["a", "b"]), encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_academico(tmp_path)
