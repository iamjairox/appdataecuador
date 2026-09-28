"""Test de rendimiento del Modulo 9 -- Submodulo 9.16.

La especificacion pide validar "5.000 entidades, 100.000 funcionarios" --
igual que en Modulos 5/6/7/8, esos volumenes son de produccion, no de
suite de CI; aqui se escalan a cantidades que siguen ejercitando el mismo
codigo (Motor de Prioridades puro + Cola persistente real contra SQLite)
sin volver la suite fragil, con limites deliberadamente holgados. Dos
angulos: el Motor de Prioridades (dominio puro, sin IO) debe seguir
siendo O(n log n) razonable con miles de candidatos; y la Cola (con IO
real via SQLite) debe encolar/tomar un lote grande de trabajos en un
tiempo acotado, respetando el orden de prioridad en la salida."""

from __future__ import annotations

import time
from datetime import UTC, datetime

from govdata.application.services.cola_trabajos_orquestador_service import (
    ColaTrabajosOrquestadorService,
)
from govdata.domain.rules.motor_prioridades_orquestador import (
    SenalesPrioridad,
    calcular_score,
    ordenar_por_prioridad,
)
from govdata.domain.rules.reglas_orquestador import ReglasPrioridadEjecucion
from govdata.domain.value_objects.nivel_prioridad_ejecucion import NivelPrioridadEjecucion
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_trabajo_orquestador_repository import (
    SqlAlchemyTrabajoOrquestadorRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_REGLAS = ReglasPrioridadEjecucion()


def _senales_sinteticas(indice: int) -> SenalesPrioridad:
    return SenalesPrioridad(
        tiempo_sin_actualizacion_horas=float(indice % 72),
        cantidad_funcionarios=indice % 200,
        alertas_pendientes=indice % 3,
        cambios_recientes=indice % 5,
        errores_anteriores=indice % 7,
    )


def test_motor_prioridades_no_degrada_con_miles_de_entidades() -> None:
    cantidad = 5_000
    candidatos = list(range(cantidad))

    inicio = time.perf_counter()
    ordenados = ordenar_por_prioridad(candidatos, _senales_sinteticas, _REGLAS)
    duracion = time.perf_counter() - inicio

    assert len(ordenados) == cantidad
    scores = [calcular_score(_senales_sinteticas(i), _REGLAS) for i in ordenados]
    assert scores == sorted(scores, reverse=True)
    assert duracion < 10.0, f"Priorizar {cantidad} entidades tardo {duracion:.2f}s (limite: 10s)"


def test_cola_encola_y_toma_un_lote_grande_respetando_prioridad(sesion) -> None:
    cantidad = 1_000
    cola = ColaTrabajosOrquestadorService(SqlAlchemyTrabajoOrquestadorRepository(sesion), ahora_provider=lambda: _AHORA)

    inicio_encolar = time.perf_counter()
    for i in range(cantidad):
        prioridad = NivelPrioridadEjecucion.MUY_ALTA if i % 100 == 0 else NivelPrioridadEjecucion.BAJA
        cola.encolar(
            TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": f"Entidad {i}"}, "consulta_rapida",
            prioridad=prioridad,
        )
    duracion_encolar = time.perf_counter() - inicio_encolar
    assert duracion_encolar < 30.0, f"Encolar {cantidad} trabajos tardo {duracion_encolar:.2f}s (limite: 30s)"

    inicio_tomar = time.perf_counter()
    tomados: list[NivelPrioridadEjecucion] = []
    while len(tomados) < cantidad:
        trabajo = cola.tomar_siguiente()
        assert trabajo is not None
        tomados.append(trabajo.prioridad)
    duracion_tomar = time.perf_counter() - inicio_tomar

    assert len(tomados) == cantidad
    # Las 10 primeras tomas deben ser MUY_ALTA (el 1% de prioridad alta
    # sale primero, exactamente lo que 9.5 promete).
    assert tomados[:10] == [NivelPrioridadEjecucion.MUY_ALTA] * 10
    assert duracion_tomar < 60.0, f"Tomar {cantidad} trabajos tardo {duracion_tomar:.2f}s (limite: 60s)"
