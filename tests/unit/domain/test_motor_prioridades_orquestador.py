"""Tests: Motor de Prioridades del Orquestador -- Submodulo 9.5."""

from __future__ import annotations

from govdata.domain.rules.motor_prioridades_orquestador import (
    SenalesPrioridad,
    calcular_prioridad,
    calcular_score,
    ordenar_por_prioridad,
)
from govdata.domain.rules.reglas_orquestador import ReglasPrioridadEjecucion
from govdata.domain.value_objects.nivel_prioridad_ejecucion import NivelPrioridadEjecucion

_REGLAS = ReglasPrioridadEjecucion(
    peso_tiempo_sin_actualizacion=1.0, peso_cantidad_funcionarios=1.0, peso_alertas_pendientes=2.0,
    peso_cambios_recientes=1.5, peso_errores_anteriores=1.0, umbral_muy_alta=80.0, umbral_alta=50.0,
    umbral_media=20.0, horas_referencia_actualizacion=24.0, funcionarios_referencia=50,
)


class TestCalcularScore:
    def test_sin_senales_score_cero(self) -> None:
        assert calcular_score(SenalesPrioridad(), _REGLAS) == 0.0

    def test_todas_las_senales_al_maximo_score_100(self) -> None:
        senales = SenalesPrioridad(
            tiempo_sin_actualizacion_horas=48, cantidad_funcionarios=100, alertas_pendientes=5,
            cambios_recientes=3, errores_anteriores=2,
        )
        assert calcular_score(senales, _REGLAS) == 100.0

    def test_alerta_pendiente_satura_sin_importar_cantidad(self) -> None:
        una = calcular_score(SenalesPrioridad(alertas_pendientes=1), _REGLAS)
        diez = calcular_score(SenalesPrioridad(alertas_pendientes=10), _REGLAS)
        assert una == diez

    def test_tiempo_sin_actualizacion_escala_linealmente(self) -> None:
        mitad = calcular_score(SenalesPrioridad(tiempo_sin_actualizacion_horas=12), _REGLAS)
        completo = calcular_score(SenalesPrioridad(tiempo_sin_actualizacion_horas=24), _REGLAS)
        assert 0 < mitad < completo


class TestCalcularPrioridad:
    def test_score_alto_es_muy_alta(self) -> None:
        senales = SenalesPrioridad(
            tiempo_sin_actualizacion_horas=24, cantidad_funcionarios=50, alertas_pendientes=1, cambios_recientes=1,
        )
        assert calcular_prioridad(senales, _REGLAS) == NivelPrioridadEjecucion.MUY_ALTA

    def test_score_medio_alto_es_alta(self) -> None:
        # (peso_alertas + peso_cambios) / peso_total = (2.0 + 1.5) / 6.5 = 53.8% -> ALTA [50, 80).
        senales = SenalesPrioridad(alertas_pendientes=1, cambios_recientes=1)
        assert calcular_prioridad(senales, _REGLAS) == NivelPrioridadEjecucion.ALTA

    def test_score_bajo_pero_no_cero_es_media(self) -> None:
        # peso_alertas / peso_total = 2.0 / 6.5 = 30.8% -> MEDIA [20, 50).
        senales = SenalesPrioridad(alertas_pendientes=1)
        assert calcular_prioridad(senales, _REGLAS) == NivelPrioridadEjecucion.MEDIA

    def test_sin_senales_es_baja(self) -> None:
        assert calcular_prioridad(SenalesPrioridad(), _REGLAS) == NivelPrioridadEjecucion.BAJA


class TestCasosBordeCalcularScore:
    def test_referencia_cero_no_divide_por_cero(self) -> None:
        reglas = ReglasPrioridadEjecucion(horas_referencia_actualizacion=0.0, funcionarios_referencia=0)
        senales = SenalesPrioridad(tiempo_sin_actualizacion_horas=10, cantidad_funcionarios=5)
        # Con referencia 0, esas dos senales normalizan a 0.0 (no ZeroDivisionError).
        assert calcular_score(senales, reglas) == 0.0

    def test_peso_total_cero_retorna_cero(self) -> None:
        reglas = ReglasPrioridadEjecucion(
            peso_tiempo_sin_actualizacion=0.0, peso_cantidad_funcionarios=0.0, peso_alertas_pendientes=0.0,
            peso_cambios_recientes=0.0, peso_errores_anteriores=0.0,
        )
        senales = SenalesPrioridad(alertas_pendientes=1, cambios_recientes=1, errores_anteriores=1)
        assert calcular_score(senales, reglas) == 0.0


class TestOrdenarPorPrioridad:
    def test_ordena_de_mayor_a_menor(self) -> None:
        candidatos = [
            ("baja", SenalesPrioridad()),
            ("alta", SenalesPrioridad(alertas_pendientes=1, cambios_recientes=1)),
        ]
        ordenados = ordenar_por_prioridad(candidatos, lambda c: c[1], _REGLAS)
        assert ordenados[0][0] == "alta"
        assert ordenados[1][0] == "baja"
