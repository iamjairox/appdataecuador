"""Tests: `cargar_rule_engine` (Motor de Reglas, Submodulos 4.x y 5.x) --
validacion de los cuatro YAML de `config/rules/` y sus casos de error."""

from __future__ import annotations

from pathlib import Path

import pytest

from govdata.config.rule_engine import cargar_rule_engine
from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError

_SINONIMOS_VALIDO = """
campos:
  nombres: ["Nombres"]
  apellidos: ["Apellidos"]
"""
_CLASIFICACION_VALIDA = """
umbral_score_minimo: 80.0
niveles_confianza:
  alta: 92.0
  media: 80.0
areas:
  juridica:
    cargos: ["Director Juridico"]
"""
_VIGENCIA_VALIDA = """
dias_vigencia: 1
"""
_CRITICIDAD_VALIDA = """
umbral_score_minimo: 80.0
niveles:
  critico:
    cargos: ["Director Juridico"]
  alto:
    cargos: ["Abogado"]
  medio:
    campos: ["correo", "telefono"]
umbral_cambio_masivo_pct: 30.0
"""


def _escribir_reglas_validas(directorio: Path) -> None:
    (directorio / "sinonimos_campos.yaml").write_text(_SINONIMOS_VALIDO, encoding="utf-8")
    (directorio / "clasificacion_areas.yaml").write_text(_CLASIFICACION_VALIDA, encoding="utf-8")
    (directorio / "vigencia_cache.yaml").write_text(_VIGENCIA_VALIDA, encoding="utf-8")
    (directorio / "criticidad_cambios.yaml").write_text(_CRITICIDAD_VALIDA, encoding="utf-8")


class TestCargarRuleEngineExitoso:
    def test_carga_los_tres_archivos_y_construye_el_rule_engine(self, tmp_path: Path) -> None:
        _escribir_reglas_validas(tmp_path)
        motor = cargar_rule_engine(tmp_path)

        assert motor.normalizacion.sinonimos_por_campo["nombres"] == ["Nombres"]
        assert motor.clasificacion.cargos_por_area["juridica"] == ["Director Juridico"]
        assert motor.clasificacion.nivel_alta == 92.0
        assert motor.cache.dias_vigencia == 1
        assert motor.criticidad.cargos_criticos == ["Director Juridico"]
        assert motor.criticidad.umbral_cambio_masivo_pct == 30.0

    def test_acepta_directorio_como_str(self, tmp_path: Path) -> None:
        _escribir_reglas_validas(tmp_path)
        motor = cargar_rule_engine(str(tmp_path))
        assert motor.cache.dias_vigencia == 1

    def test_valores_por_defecto_cuando_faltan_claves_opcionales(self, tmp_path: Path) -> None:
        (tmp_path / "sinonimos_campos.yaml").write_text(_SINONIMOS_VALIDO, encoding="utf-8")
        (tmp_path / "clasificacion_areas.yaml").write_text("areas:\n  juridica:\n    cargos: []\n", encoding="utf-8")
        (tmp_path / "vigencia_cache.yaml").write_text("{}\n", encoding="utf-8")
        (tmp_path / "criticidad_cambios.yaml").write_text("niveles:\n  critico:\n    cargos: []\n", encoding="utf-8")

        motor = cargar_rule_engine(tmp_path)
        assert motor.clasificacion.umbral_score_minimo == 80.0
        assert motor.clasificacion.nivel_alta == 92.0
        assert motor.cache.dias_vigencia == 1
        assert motor.criticidad.umbral_cambio_masivo_pct == 30.0


class TestCargarRuleEngineErrores:
    def test_archivo_inexistente_lanza_configuracion_invalida(self, tmp_path: Path) -> None:
        with pytest.raises(ConfiguracionInvalidaError, match="no encontrado"):
            cargar_rule_engine(tmp_path)

    def test_yaml_malformado_lanza_configuracion_invalida(self, tmp_path: Path) -> None:
        (tmp_path / "sinonimos_campos.yaml").write_text("campos: [no cierra\n", encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError, match="YAML invalido"):
            cargar_rule_engine(tmp_path)

    def test_raiz_no_es_un_mapeo_lanza_configuracion_invalida(self, tmp_path: Path) -> None:
        (tmp_path / "sinonimos_campos.yaml").write_text("- item1\n- item2\n", encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError, match="mapeo YAML"):
            cargar_rule_engine(tmp_path)

    def test_sinonimos_sin_clave_campos_lanza_configuracion_invalida(self, tmp_path: Path) -> None:
        (tmp_path / "sinonimos_campos.yaml").write_text("otra_clave: 1\n", encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError, match="campos"):
            cargar_rule_engine(tmp_path)

    def test_clasificacion_sin_clave_areas_lanza_configuracion_invalida(self, tmp_path: Path) -> None:
        (tmp_path / "sinonimos_campos.yaml").write_text(_SINONIMOS_VALIDO, encoding="utf-8")
        (tmp_path / "clasificacion_areas.yaml").write_text("otra_clave: 1\n", encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError, match="areas"):
            cargar_rule_engine(tmp_path)

    def test_criticidad_sin_clave_niveles_lanza_configuracion_invalida(self, tmp_path: Path) -> None:
        (tmp_path / "sinonimos_campos.yaml").write_text(_SINONIMOS_VALIDO, encoding="utf-8")
        (tmp_path / "clasificacion_areas.yaml").write_text(_CLASIFICACION_VALIDA, encoding="utf-8")
        (tmp_path / "vigencia_cache.yaml").write_text(_VIGENCIA_VALIDA, encoding="utf-8")
        (tmp_path / "criticidad_cambios.yaml").write_text("otra_clave: 1\n", encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError, match="niveles"):
            cargar_rule_engine(tmp_path)

    def test_criticidad_archivo_inexistente_lanza_configuracion_invalida(self, tmp_path: Path) -> None:
        (tmp_path / "sinonimos_campos.yaml").write_text(_SINONIMOS_VALIDO, encoding="utf-8")
        (tmp_path / "clasificacion_areas.yaml").write_text(_CLASIFICACION_VALIDA, encoding="utf-8")
        (tmp_path / "vigencia_cache.yaml").write_text(_VIGENCIA_VALIDA, encoding="utf-8")
        with pytest.raises(ConfiguracionInvalidaError, match="no encontrado"):
            cargar_rule_engine(tmp_path)

    def test_usa_el_directorio_por_defecto_del_proyecto_si_no_se_indica(self) -> None:
        """Sin `directorio_reglas`, debe leer `config/rules/` real del
        proyecto (los mismos YAML que usa produccion)."""
        motor = cargar_rule_engine()
        assert motor.clasificacion.cargos_por_area  # trae datos reales, no vacio
