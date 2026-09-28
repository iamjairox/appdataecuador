"""Tests de integracion de persistencia -- los 2 repositorios nuevos del
Modulo 9 (`TrabajoOrquestador`, `AuditoriaEtapa`) contra SQLite real.
Mismo espiritu que `test_persistencia_modulo8.py`: prueba el mapeo ORM
<-> dominio, la migracion 0009, y (critico para el Submodulo 9.8) que
`tomar_atomico` produce un `UPDATE ... WHERE version_lock = ?` real, no
solo la version simulada por `FakeTrabajoOrquestadorRepository`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from govdata.domain.entities.auditoria_etapa import AuditoriaEtapa
from govdata.domain.entities.trabajo_orquestador import TrabajoOrquestador
from govdata.domain.value_objects.estado_paso import EstadoPaso
from govdata.domain.value_objects.estado_trabajo_orquestador import EstadoTrabajoOrquestador
from govdata.domain.value_objects.nivel_prioridad_ejecucion import NivelPrioridadEjecucion
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_auditoria_etapa_repository import (
    SqlAlchemyAuditoriaEtapaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_trabajo_orquestador_repository import (
    SqlAlchemyTrabajoOrquestadorRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _trabajo(
    tipo: TipoTrabajoOrquestador = TipoTrabajoOrquestador.CONSULTA_ENTIDAD,
    estado: EstadoTrabajoOrquestador = EstadoTrabajoOrquestador.EN_COLA,
    prioridad: NivelPrioridadEjecucion = NivelPrioridadEjecucion.MEDIA,
    creado_en: datetime = _AHORA,
) -> TrabajoOrquestador:
    return TrabajoOrquestador(
        tipo=tipo, parametros={"nombre_entidad": "Procuraduria"}, estado=estado, prioridad=prioridad,
        creado_en=creado_en, actualizado_en=creado_en,
    )


class TestSqlAlchemyTrabajoOrquestadorRepository:
    def test_guardar_y_recuperar_por_id_preserva_todos_los_campos(self, sesion) -> None:
        repo = SqlAlchemyTrabajoOrquestadorRepository(sesion)
        original = _trabajo()
        guardado = repo.guardar(original)

        recuperado = repo.buscar_por_id(guardado.id)
        assert recuperado is not None
        assert recuperado.id == guardado.id
        assert recuperado.tipo == TipoTrabajoOrquestador.CONSULTA_ENTIDAD
        assert recuperado.estado == EstadoTrabajoOrquestador.EN_COLA
        assert recuperado.parametros == {"nombre_entidad": "Procuraduria"}
        assert recuperado.version_lock == 1

    def test_buscar_por_id_inexistente_retorna_none(self, sesion) -> None:
        import uuid

        repo = SqlAlchemyTrabajoOrquestadorRepository(sesion)
        assert repo.buscar_por_id(uuid.uuid4()) is None

    def test_guardar_sin_creado_en_no_lo_inventa(self, sesion) -> None:
        """El mapper solo escribe `creado_en` cuando el dominio lo trae
        (no lo pisa con `None` en una actualizacion, ni lo inventa en una
        insercion sin ese dato)."""
        repo = SqlAlchemyTrabajoOrquestadorRepository(sesion)
        trabajo = TrabajoOrquestador(
            tipo=TipoTrabajoOrquestador.CONSULTA_ENTIDAD, estado=EstadoTrabajoOrquestador.EN_COLA,
        )
        assert trabajo.creado_en is None

        guardado = repo.guardar(trabajo)

        recuperado = repo.buscar_por_id(guardado.id)
        assert recuperado is not None
        assert recuperado.creado_en is None

    def test_listar_por_estado(self, sesion) -> None:
        repo = SqlAlchemyTrabajoOrquestadorRepository(sesion)
        repo.guardar(_trabajo(estado=EstadoTrabajoOrquestador.EN_COLA))
        repo.guardar(_trabajo(estado=EstadoTrabajoOrquestador.EN_COLA))
        repo.guardar(_trabajo(estado=EstadoTrabajoOrquestador.COMPLETADO))

        en_cola = repo.listar_por_estado(EstadoTrabajoOrquestador.EN_COLA)
        assert len(en_cola) == 2
        assert all(t.estado == EstadoTrabajoOrquestador.EN_COLA for t in en_cola)

    def test_listar_pendientes_ordenados_por_prioridad(self, sesion) -> None:
        repo = SqlAlchemyTrabajoOrquestadorRepository(sesion)
        baja = repo.guardar(_trabajo(prioridad=NivelPrioridadEjecucion.BAJA, creado_en=_AHORA))
        muy_alta = repo.guardar(_trabajo(prioridad=NivelPrioridadEjecucion.MUY_ALTA, creado_en=_AHORA + timedelta(seconds=1)))
        media = repo.guardar(_trabajo(prioridad=NivelPrioridadEjecucion.MEDIA, creado_en=_AHORA + timedelta(seconds=2)))
        # No debe aparecer -- ya EJECUTANDO, no es candidato.
        repo.guardar(_trabajo(estado=EstadoTrabajoOrquestador.EJECUTANDO))

        pendientes = repo.listar_pendientes_ordenados_por_prioridad()

        assert [t.id for t in pendientes] == [muy_alta.id, media.id, baja.id]

    def test_contar_por_estado(self, sesion) -> None:
        repo = SqlAlchemyTrabajoOrquestadorRepository(sesion)
        repo.guardar(_trabajo(estado=EstadoTrabajoOrquestador.EN_COLA))
        repo.guardar(_trabajo(estado=EstadoTrabajoOrquestador.EN_COLA))
        repo.guardar(_trabajo(estado=EstadoTrabajoOrquestador.COMPLETADO))

        conteos = repo.contar_por_estado()

        assert conteos[EstadoTrabajoOrquestador.EN_COLA] == 2
        assert conteos[EstadoTrabajoOrquestador.COMPLETADO] == 1

    def test_tomar_atomico_exitoso_actualiza_estado_y_version(self, sesion) -> None:
        repo = SqlAlchemyTrabajoOrquestadorRepository(sesion)
        trabajo = repo.guardar(_trabajo(estado=EstadoTrabajoOrquestador.EN_COLA))

        gano = repo.tomar_atomico(trabajo.id, trabajo.version_lock)

        assert gano is True
        recargado = repo.buscar_por_id(trabajo.id)
        assert recargado is not None
        assert recargado.estado == EstadoTrabajoOrquestador.EJECUTANDO
        assert recargado.version_lock == trabajo.version_lock + 1

    def test_tomar_atomico_falla_si_version_ya_avanzo(self, sesion) -> None:
        """Simula la carrera real (Submodulo 9.8): un worker ya gano el
        bloqueo (avanzo `version_lock` con un `UPDATE` real) antes de que
        el segundo intente el suyo con la version VIEJA que aun tenia en
        memoria."""
        repo = SqlAlchemyTrabajoOrquestadorRepository(sesion)
        trabajo = repo.guardar(_trabajo(estado=EstadoTrabajoOrquestador.EN_COLA))
        version_original = trabajo.version_lock

        assert repo.tomar_atomico(trabajo.id, version_original) is True
        # Un segundo worker, que leyo el trabajo ANTES del UPDATE de arriba,
        # todavia cree que la version es la original -- debe perder.
        perdio = repo.tomar_atomico(trabajo.id, version_original)

        assert perdio is False
        recargado = repo.buscar_por_id(trabajo.id)
        assert recargado is not None
        assert recargado.estado == EstadoTrabajoOrquestador.EJECUTANDO
        assert recargado.version_lock == version_original + 1


class TestSqlAlchemyAuditoriaEtapaRepository:
    def test_guardar_lote_y_listar_por_trabajo(self, sesion) -> None:
        trabajo_repo = SqlAlchemyTrabajoOrquestadorRepository(sesion)
        trabajo = trabajo_repo.guardar(_trabajo())

        repo = SqlAlchemyAuditoriaEtapaRepository(sesion)
        repo.guardar_lote(
            [
                AuditoriaEtapa(
                    trabajo_orquestador_id=str(trabajo.id), tipo_paso=TipoPasoPipeline.DESCUBRIMIENTO,
                    estado_paso=EstadoPaso.EJECUTADO, iniciado_en=_AHORA, finalizado_en=_AHORA, cantidad_registros=3,
                ),
                AuditoriaEtapa(
                    trabajo_orquestador_id=str(trabajo.id), tipo_paso=TipoPasoPipeline.SENESCYT,
                    estado_paso=EstadoPaso.OMITIDO, iniciado_en=_AHORA, finalizado_en=_AHORA,
                    razon_omision="cache_vigente",
                ),
            ]
        )

        etapas = repo.listar_por_trabajo(str(trabajo.id))
        assert len(etapas) == 2
        por_paso = {e.tipo_paso: e for e in etapas}
        assert por_paso[TipoPasoPipeline.DESCUBRIMIENTO].estado_paso == EstadoPaso.EJECUTADO
        assert por_paso[TipoPasoPipeline.DESCUBRIMIENTO].cantidad_registros == 3
        assert por_paso[TipoPasoPipeline.SENESCYT].razon_omision == "cache_vigente"

    def test_listar_todo(self, sesion) -> None:
        trabajo_repo = SqlAlchemyTrabajoOrquestadorRepository(sesion)
        trabajo_a = trabajo_repo.guardar(_trabajo())
        trabajo_b = trabajo_repo.guardar(_trabajo())

        repo = SqlAlchemyAuditoriaEtapaRepository(sesion)
        repo.guardar_lote(
            [
                AuditoriaEtapa(
                    trabajo_orquestador_id=str(trabajo_a.id), tipo_paso=TipoPasoPipeline.FORO,
                    estado_paso=EstadoPaso.EJECUTADO, iniciado_en=_AHORA, finalizado_en=_AHORA,
                ),
                AuditoriaEtapa(
                    trabajo_orquestador_id=str(trabajo_b.id), tipo_paso=TipoPasoPipeline.PERFIL,
                    estado_paso=EstadoPaso.EJECUTADO, iniciado_en=_AHORA, finalizado_en=_AHORA,
                ),
            ]
        )

        assert len(repo.listar_todo()) == 2
