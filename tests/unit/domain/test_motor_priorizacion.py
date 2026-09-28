"""Tests: Motor de Priorizacion (Submodulo 6.11)."""

from __future__ import annotations

from govdata.domain.rules.motor_priorizacion import calcular_prioridad, ordenar_por_prioridad
from govdata.domain.rules.reglas_identidad import ReglasPriorizacion

_REGLAS = ReglasPriorizacion(
    prioridad_por_cargo={
        "Director Juridico": 100.0,
        "Procurador": 95.0,
        "Director Financiero": 90.0,
        "Asesor Juridico": 85.0,
        "Abogado": 80.0,
    },
    prioridad_defecto=10.0,
    umbral_score_minimo=80.0,
)


class TestCalcularPrioridad:
    def test_cargo_reconocido_exacto(self) -> None:
        assert calcular_prioridad("Director Juridico", _REGLAS) == 100.0

    def test_cargo_no_reconocido_usa_prioridad_por_defecto(self) -> None:
        assert calcular_prioridad("Conserje", _REGLAS) == 10.0

    def test_cargo_none_usa_prioridad_por_defecto(self) -> None:
        assert calcular_prioridad(None, _REGLAS) == 10.0

    def test_variacion_menor_de_escritura_sigue_reconocida(self) -> None:
        assert calcular_prioridad("director juridico", _REGLAS) == 100.0


class TestOrdenarPorPrioridad:
    def test_ordena_de_mayor_a_menor_prioridad(self) -> None:
        candidatos = ["c1", "c2", "c3", "c4"]
        cargos = {"c1": "Abogado", "c2": "Director Juridico", "c3": "Conserje", "c4": "Procurador"}
        resultado = ordenar_por_prioridad(candidatos, lambda c: cargos[c], _REGLAS)
        assert resultado == ["c2", "c4", "c1", "c3"]

    def test_no_consulta_todos_primero_sin_orden_el_menos_prioritario_queda_ultimo(self) -> None:
        candidatos = ["chofer", "director"]
        cargos = {"chofer": "Chofer", "director": "Director Juridico"}
        resultado = ordenar_por_prioridad(candidatos, lambda c: cargos[c], _REGLAS)
        assert resultado[0] == "director"


class TestPrioridadConReglasReales:
    """`config/rules/priorizacion_cargos.yaml` real contra cargos reales del
    numeral 2 DPE (muestreo 2026-09-27)."""

    @staticmethod
    def _prioridad(cargo: str) -> float:
        from govdata.config.rule_engine_identidad import cargar_rule_engine_identidad

        return calcular_prioridad(cargo, cargar_rule_engine_identidad().priorizacion)

    def test_orden_de_contacto_juridico(self) -> None:
        cargos_en_orden = [
            "PROCURADOR SINDICO",
            "DIRECTOR JURIDICO",
            "DIRECTOR/A DE ASESORIA JURIDICA",
            "COORDINADOR/A GENERAL JURIDICO/A",
            "JEFE DE PATROCINIO",
            "ASESOR JURIDICO 2",
            "ANALISTA JURIDICO ZONAL 2",
            "ABOGADO JUNIOR",
            "CONSERJE",
        ]
        prioridades = [self._prioridad(c) for c in cargos_en_orden]
        assert prioridades == sorted(prioridades, reverse=True)
        assert len(set(prioridades)) == len(prioridades)

    def test_subprocurador_por_debajo_del_procurador(self) -> None:
        assert self._prioridad("SUB PROCURADOR SINDICO") < self._prioridad("PROCURADORA SÍNDICA MUNICIPAL")

    def test_cargo_no_juridico_conserva_prioridad_por_defecto(self) -> None:
        assert self._prioridad("AGENTE MUNICIPAL") == 10.0
