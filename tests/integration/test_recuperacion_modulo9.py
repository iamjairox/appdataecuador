"""Test de integracion -- Submodulo 9.7 (Reanudacion automatica): "Si el
servidor se apaga. Al reiniciar. Debe continuar exactamente donde
quedo." Se simula la caida escribiendo un `TrabajoOrquestador` en estado
EJECUTANDO directamente en una sesion, cerrandola (representa el proceso
que murio sin marcar COMPLETADO/ERROR), y verificando en una sesion
NUEVA (representa el reinicio) que `reanudar_interrumpidos()` lo
reencola -- contra SQLite real, no el fake."""

from __future__ import annotations

from datetime import UTC, datetime

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


def _trabajo(estado: EstadoTrabajoOrquestador) -> TrabajoOrquestador:
    return TrabajoOrquestador(
        tipo=TipoTrabajoOrquestador.CONSULTA_ENTIDAD, parametros={"nombre_entidad": "Procuraduria"},
        estado=estado, creado_en=_AHORA, actualizado_en=_AHORA,
    )


def test_trabajos_ejecutando_se_reencolan_tras_reinicio_simulado(sqlite_engine) -> None:
    from sqlalchemy.orm import sessionmaker

    Factory = sessionmaker(bind=sqlite_engine, future=True)

    # -- "Proceso original", muere a mitad de un trabajo (nunca llega a --
    # -- marcar COMPLETADO/ERROR) -- la sesion se cierra sin mas. --------
    sesion_original = Factory()
    interrumpido = SqlAlchemyTrabajoOrquestadorRepository(sesion_original).guardar(
        _trabajo(EstadoTrabajoOrquestador.EJECUTANDO)
    )
    sesion_original.commit()
    sesion_original.close()

    # -- "Reinicio del servidor": sesion completamente NUEVA. ------------
    sesion_nueva = Factory()
    try:
        cola = ColaTrabajosOrquestadorService(SqlAlchemyTrabajoOrquestadorRepository(sesion_nueva))
        cantidad = cola.reanudar_interrumpidos()
        sesion_nueva.commit()
        assert cantidad == 1

        recargado = cola.buscar_por_id(interrumpido.id)
        assert recargado is not None
        assert recargado.estado == EstadoTrabajoOrquestador.EN_COLA
    finally:
        sesion_nueva.close()


def test_trabajos_no_ejecutando_no_se_tocan(sqlite_engine) -> None:
    from sqlalchemy.orm import sessionmaker

    Factory = sessionmaker(bind=sqlite_engine, future=True)
    sesion_setup = Factory()
    repo_setup = SqlAlchemyTrabajoOrquestadorRepository(sesion_setup)
    en_cola = repo_setup.guardar(_trabajo(EstadoTrabajoOrquestador.EN_COLA))
    completado = repo_setup.guardar(_trabajo(EstadoTrabajoOrquestador.COMPLETADO))
    sesion_setup.commit()
    sesion_setup.close()

    sesion_nueva = Factory()
    try:
        cola = ColaTrabajosOrquestadorService(SqlAlchemyTrabajoOrquestadorRepository(sesion_nueva))
        assert cola.reanudar_interrumpidos() == 0

        assert cola.buscar_por_id(en_cola.id).estado == EstadoTrabajoOrquestador.EN_COLA  # type: ignore[union-attr]
        assert cola.buscar_por_id(completado.id).estado == EstadoTrabajoOrquestador.COMPLETADO  # type: ignore[union-attr]
    finally:
        sesion_nueva.close()


def test_reanudar_interrumpidos_es_idempotente(sqlite_engine) -> None:
    """Correr `reanudar_interrumpidos()` dos veces seguidas (ej. dos
    reinicios en cadena) no debe reencolar nada la segunda vez -- ya no
    hay nada en EJECUTANDO."""
    from sqlalchemy.orm import sessionmaker

    Factory = sessionmaker(bind=sqlite_engine, future=True)
    sesion_setup = Factory()
    SqlAlchemyTrabajoOrquestadorRepository(sesion_setup).guardar(_trabajo(EstadoTrabajoOrquestador.EJECUTANDO))
    sesion_setup.commit()
    sesion_setup.close()

    sesion = Factory()
    try:
        cola = ColaTrabajosOrquestadorService(SqlAlchemyTrabajoOrquestadorRepository(sesion))
        assert cola.reanudar_interrumpidos() == 1
        sesion.commit()
        assert cola.reanudar_interrumpidos() == 0
    finally:
        sesion.close()
