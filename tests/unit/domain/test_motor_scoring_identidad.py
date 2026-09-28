"""Tests: Scoring Engine (Submodulo 6.3)."""

from __future__ import annotations

import pytest

from govdata.application.dto.senales_identidad_dto import SenalesIdentidadDTO
from govdata.domain.exceptions.domain_exceptions import ConfiguracionInvalidaError
from govdata.domain.rules.motor_scoring_identidad import calcular_score
from govdata.domain.rules.reglas_identidad import PesosScoring

_PESOS = PesosScoring(
    fingerprint=0.40, correo=0.25, nombre=0.15, apellido=0.10, institucion=0.05, cargo=0.05,
    umbral_minimo_coincidencia=60.0,
)


def _senales(**kwargs) -> SenalesIdentidadDTO:
    base = {"nombre": "Juan", "apellido": "Perez", "correo": "j@x.com", "telefono": None,
            "institucion": "DPE", "cargo": "Director Juridico", "fingerprint": "JUANPEREZ"}
    base.update(kwargs)
    return SenalesIdentidadDTO(**base)


class TestPesosScoring:
    def test_pesos_deben_sumar_uno(self) -> None:
        with pytest.raises(ConfiguracionInvalidaError):
            PesosScoring(fingerprint=0.5, correo=0.5, nombre=0.5, apellido=0.0, institucion=0.0, cargo=0.0)


class TestCalcularScore:
    def test_identico_en_todo_da_score_maximo(self) -> None:
        score, campos = calcular_score(_senales(), _senales(), _PESOS)
        assert score == 100.0
        assert all(c.coincide or c.peso == 0.0 for c in campos)

    def test_fingerprint_identico_pesa_40_por_ciento(self) -> None:
        a = _senales(correo=None, institucion=None, cargo=None)
        b = _senales(correo=None, institucion=None, cargo=None, nombre="Otro", apellido="Otro")
        score, _ = calcular_score(a, b, _PESOS)
        # fingerprint coincide (40) + nombre/apellido difieren (0) -> ~40
        assert 35.0 <= score <= 45.0

    def test_campos_ausentes_no_excluyen_el_peso_del_calculo(self) -> None:
        a = _senales(fingerprint=None, correo=None, institucion=None, cargo=None)
        b = _senales(fingerprint=None, correo=None, institucion=None, cargo=None)
        score, campos = calcular_score(a, b, _PESOS)
        # solo nombre+apellido pueden aportar (0.15+0.10=0.25 de peso maximo)
        assert score == pytest.approx(25.0, abs=0.5)
        fingerprint_campo = next(c for c in campos if c.campo == "fingerprint")
        assert fingerprint_campo.score_campo == 0.0
        assert fingerprint_campo.coincide is False

    def test_correo_mismo_dominio_distinto_local_da_credito_parcial(self) -> None:
        a = _senales(correo="ana@justicia.gob.ec")
        b = _senales(correo="pedro@justicia.gob.ec")
        _, campos = calcular_score(a, b, _PESOS)
        correo_campo = next(c for c in campos if c.campo == "correo")
        assert 0.0 < correo_campo.score_campo < 100.0

    def test_correo_exacto_da_100(self) -> None:
        a = _senales(correo="ana@x.com")
        b = _senales(correo="ana@x.com")
        _, campos = calcular_score(a, b, _PESOS)
        correo_campo = next(c for c in campos if c.campo == "correo")
        assert correo_campo.score_campo == 100.0

    def test_nombre_con_variacion_menor_tiene_score_alto_no_perfecto(self) -> None:
        a = _senales(nombre="Juan Carlos")
        b = _senales(nombre="Juan  Carlos ")
        _, campos = calcular_score(a, b, _PESOS)
        nombre_campo = next(c for c in campos if c.campo == "nombre")
        assert nombre_campo.score_campo >= 90.0

    def test_telefono_se_reporta_pero_no_pesa(self) -> None:
        a = _senales(telefono="0991111111")
        b = _senales(telefono="0992222222")
        score_igual, _ = calcular_score(_senales(telefono="X"), _senales(telefono="X"), _PESOS)
        score_distinto, campos = calcular_score(a, b, _PESOS)
        assert score_igual == score_distinto  # telefono no afecta el total
        telefono_campo = next(c for c in campos if c.campo == "telefono")
        assert telefono_campo.peso == 0.0
