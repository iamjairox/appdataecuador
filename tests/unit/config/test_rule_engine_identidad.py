"""Tests: cargador del Motor de Reglas del Modulo 6 (config/rule_engine_identidad.py)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad
from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError


def _escribir_yaml_validos(directorio: Path) -> None:
    (directorio / "scoring_identidad.yaml").write_text(
        yaml.safe_dump(
            {
                "pesos": {
                    "fingerprint": 0.40, "correo": 0.25, "nombre": 0.15,
                    "apellido": 0.10, "institucion": 0.05, "cargo": 0.05,
                },
                "umbral_minimo_coincidencia": 60.0,
            }
        ),
        encoding="utf-8",
    )
    (directorio / "confianza_fusion.yaml").write_text(
        yaml.safe_dump({"umbral_fusion_automatica": 98.0, "umbral_revision_manual": 85.0}), encoding="utf-8"
    )
    (directorio / "cache_por_fuente.yaml").write_text(
        yaml.safe_dump({"fuentes": {"senescyt": 30, "foro_abogados": 7}, "dias_defecto": 7}), encoding="utf-8"
    )
    (directorio / "priorizacion_cargos.yaml").write_text(
        yaml.safe_dump({"prioridades": {"Director Juridico": 100}, "prioridad_defecto": 10.0}), encoding="utf-8"
    )


class TestCargarRuleEngineIdentidad:
    def test_carga_los_yaml_del_proyecto_por_defecto(self) -> None:
        engine = cargar_rule_engine_identidad()
        assert engine.scoring.fingerprint == 0.40
        assert engine.fusion.umbral_fusion_automatica == 98.0
        assert engine.cache_por_fuente.dias_vigencia("senescyt") == 30
        # Seccion 12: el Procurador Sindico (reglas por palabras, 100) va por
        # encima del Director Juridico.
        assert engine.priorizacion.prioridad_por_cargo["Director Juridico"] == 95.0
        assert engine.priorizacion.reglas_por_palabras

    def test_carga_directorio_alternativo(self, tmp_path: Path) -> None:
        _escribir_yaml_validos(tmp_path)
        engine = cargar_rule_engine_identidad(tmp_path)
        assert engine.scoring.correo == 0.25
        assert engine.cache_por_fuente.dias_vigencia("foro_abogados") == 7

    def test_pesos_de_scoring_faltantes_no_suman_uno_falla(self, tmp_path: Path) -> None:
        _escribir_yaml_validos(tmp_path)
        (tmp_path / "scoring_identidad.yaml").write_text(
            yaml.safe_dump({"pesos": {"fingerprint": 0.5, "correo": 0.1, "nombre": 0.1,
                                       "apellido": 0.1, "institucion": 0.1, "cargo": 0.05}}),
            encoding="utf-8",
        )
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_identidad(tmp_path)

    def test_archivo_faltante_falla(self, tmp_path: Path) -> None:
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_identidad(tmp_path)

    def test_cache_sin_clave_fuentes_falla(self, tmp_path: Path) -> None:
        _escribir_yaml_validos(tmp_path)
        (tmp_path / "cache_por_fuente.yaml").write_text(yaml.safe_dump({"dias_defecto": 7}), encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_identidad(tmp_path)

    def test_priorizacion_sin_clave_prioridades_falla(self, tmp_path: Path) -> None:
        _escribir_yaml_validos(tmp_path)
        (tmp_path / "priorizacion_cargos.yaml").write_text(
            yaml.safe_dump({"prioridad_defecto": 10.0}), encoding="utf-8"
        )
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_identidad(tmp_path)

    def test_scoring_sin_clave_pesos_falla(self, tmp_path: Path) -> None:
        _escribir_yaml_validos(tmp_path)
        (tmp_path / "scoring_identidad.yaml").write_text(
            yaml.safe_dump({"umbral_minimo_coincidencia": 60.0}), encoding="utf-8"
        )
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_identidad(tmp_path)

    def test_yaml_con_sintaxis_invalida_falla(self, tmp_path: Path) -> None:
        _escribir_yaml_validos(tmp_path)
        (tmp_path / "scoring_identidad.yaml").write_text("pesos: [no cierra\n", encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_identidad(tmp_path)

    def test_yaml_cuya_raiz_no_es_un_mapeo_falla(self, tmp_path: Path) -> None:
        _escribir_yaml_validos(tmp_path)
        (tmp_path / "scoring_identidad.yaml").write_text(yaml.safe_dump(["no", "es", "un", "mapeo"]), encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError):
            cargar_rule_engine_identidad(tmp_path)
