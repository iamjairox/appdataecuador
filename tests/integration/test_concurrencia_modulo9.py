"""Test de concurrencia REAL del Modulo 9 -- Submodulo 9.8 (bloqueo
optimista): multiples hilos, cada uno con su PROPIA `Session` SQLAlchemy
contra el MISMO archivo SQLite (mismo patron que `test_concurrencia_modulo8.py`),
compiten por tomar trabajos de la cola. Ningun trabajo debe ser tomado por
mas de un hilo -- eso es exactamente lo que `tomar_atomico` (UPDATE ...
WHERE version_lock = ?) garantiza."""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

from sqlalchemy.orm import sessionmaker

from govdata.application.services.cola_trabajos_orquestador_service import (
    ColaTrabajosOrquestadorService,
)
from govdata.domain.entities.trabajo_orquestador import TrabajoOrquestador
from govdata.domain.value_objects.estado_trabajo_orquestador import EstadoTrabajoOrquestador
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_trabajo_orquestador_repository import (
    SqlAlchemyTrabajoOrquestadorRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_CANTIDAD_HILOS = 8
_CANTIDAD_TRABAJOS = 40


def test_multiples_workers_nunca_toman_el_mismo_trabajo(sqlite_engine_multihilo) -> None:
    Factory = sessionmaker(bind=sqlite_engine_multihilo, future=True)

    sesion_setup = Factory()
    ids_creados: list[uuid.UUID] = []
    try:
        repo_setup = SqlAlchemyTrabajoOrquestadorRepository(sesion_setup)
        for i in range(_CANTIDAD_TRABAJOS):
            trabajo = TrabajoOrquestador(
                tipo=TipoTrabajoOrquestador.CONSULTA_ENTIDAD, parametros={"nombre_entidad": f"Entidad {i}"},
                estado=EstadoTrabajoOrquestador.EN_COLA, creado_en=_AHORA, actualizado_en=_AHORA,
            )
            guardado = repo_setup.guardar(trabajo)
            ids_creados.append(guardado.id)
        sesion_setup.commit()
    finally:
        sesion_setup.close()

    def _trabajador(_indice: int) -> list[uuid.UUID]:
        sesion = Factory()
        tomados: list[uuid.UUID] = []
        try:
            cola = ColaTrabajosOrquestadorService(SqlAlchemyTrabajoOrquestadorRepository(sesion))
            while True:
                trabajo = cola.tomar_siguiente()
                sesion.commit()
                if trabajo is None:
                    break
                tomados.append(trabajo.id)
            return tomados
        finally:
            sesion.close()

    with ThreadPoolExecutor(max_workers=_CANTIDAD_HILOS) as executor:
        futuros = [executor.submit(_trabajador, i) for i in range(_CANTIDAD_HILOS)]
        resultados = [f.result() for f in as_completed(futuros)]

    todos_los_tomados = [trabajo_id for tomados_por_hilo in resultados for trabajo_id in tomados_por_hilo]

    # Nunca se toma el mismo trabajo dos veces (sin duplicados entre hilos).
    assert len(todos_los_tomados) == len(set(todos_los_tomados))
    # Y, en conjunto, los hilos tomaron TODOS los trabajos -- ninguno quedo
    # sin procesar por una carrera mal resuelta.
    assert set(todos_los_tomados) == set(ids_creados)

    sesion_verificacion = Factory()
    try:
        repo_verificacion = SqlAlchemyTrabajoOrquestadorRepository(sesion_verificacion)
        conteos = repo_verificacion.contar_por_estado()
        assert conteos.get(EstadoTrabajoOrquestador.EJECUTANDO, 0) == _CANTIDAD_TRABAJOS
        assert conteos.get(EstadoTrabajoOrquestador.EN_COLA, 0) == 0
    finally:
        sesion_verificacion.close()
