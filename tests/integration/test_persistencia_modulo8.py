"""Tests de integracion de persistencia -- los 6 repositorios nuevos del
Modulo 8 (RegistroForo, RegistroForoVersion, HistorialForo, ConsultaForo,
EventoForo, AlertaForo) contra SQLite real."""

from __future__ import annotations

from datetime import UTC, date, datetime

from govdata.domain.entities.alerta_foro import AlertaForo
from govdata.domain.entities.consulta_foro import ConsultaForo
from govdata.domain.entities.evento_foro import EventoForo
from govdata.domain.entities.historial_foro import HistorialForo
from govdata.domain.entities.registro_foro import RegistroForo
from govdata.domain.entities.registro_foro_version import RegistroForoVersion
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_foro import TipoAlertaForo
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo
from govdata.domain.value_objects.tipo_evento_foro import TipoEventoForo
from govdata.infrastructure.persistence.postgresql.models.persona_model import PersonaModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_foro_repository import (
    SqlAlchemyAlertaForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_consulta_foro_repository import (
    SqlAlchemyConsultaForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_foro_repository import (
    SqlAlchemyEventoForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_historial_foro_repository import (
    SqlAlchemyHistorialForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_registro_foro_repository import (
    SqlAlchemyRegistroForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_registro_foro_version_repository import (
    SqlAlchemyRegistroForoVersionRepository,
)
from tests.integration.test_persistencia_modulo6 import _persona_master

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _persona(sesion, nombres: str = "Juan") -> int:
    modelo = PersonaModel(nombres=nombres, apellidos="Perez")
    sesion.add(modelo)
    sesion.flush()
    return modelo.id


def _persona_master_id(sesion) -> int:
    persona_id = _persona(sesion)
    pm = _persona_master(sesion, persona_id)
    return pm.id


def _consulta(sesion, persona_master_id: int) -> int:
    repo = SqlAlchemyConsultaForoRepository(sesion)
    consulta = repo.guardar(ConsultaForo(persona_master_id=persona_master_id, iniciado_en=_AHORA))
    return consulta.id


class TestSqlAlchemyConsultaForoRepository:
    def test_guardar_finalizar_y_recuperar(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        repo = SqlAlchemyConsultaForoRepository(sesion)
        consulta = repo.guardar(ConsultaForo(persona_master_id=pm_id, iniciado_en=_AHORA))
        consulta.finalizar(
            exito=True, cuando=_AHORA, duracion_segundos=2.0, respuesta_cruda={"registros": []},
            codigo_http=200, captcha_detectado=False, pagina_vacia=False,
        )
        repo.guardar(consulta)

        ultima = repo.ultima_consulta(pm_id)
        assert ultima is not None
        assert ultima.exito is True
        assert ultima.codigo_http == 200
        assert ultima.respuesta_cruda == {"registros": []}
        assert len(repo.listar_por_persona_master(pm_id)) == 1
        assert len(repo.listar_todas()) >= 1


class TestSqlAlchemyRegistroForoRepository:
    def test_guardar_y_buscar_vigente(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        consulta_id = _consulta(sesion, pm_id)
        repo = SqlAlchemyRegistroForoRepository(sesion)
        repo.guardar(
            RegistroForo(
                persona_master_id=pm_id, clave_registro="registro:r1", registro="R1", provincia="Pichincha",
                evidencia=str(consulta_id),
            )
        )
        vigente = repo.buscar_vigente_por_clave(pm_id, "registro:r1")
        assert vigente is not None
        assert len(repo.listar_vigentes_por_persona_master(pm_id)) == 1

    def test_registro_no_vigente_no_aparece_en_listado(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        repo = SqlAlchemyRegistroForoRepository(sesion)
        registro = repo.guardar(
            RegistroForo(persona_master_id=pm_id, clave_registro="registro:r1", registro="R1")
        )
        registro.cerrar()
        repo.guardar(registro)
        assert repo.listar_vigentes_por_persona_master(pm_id) == []
        assert repo.buscar_vigente_por_clave(pm_id, "registro:r1") is None


class TestSqlAlchemyRegistroForoVersionRepository:
    def test_versionado_nunca_sobreescribe(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        consulta_id = _consulta(sesion, pm_id)
        repo = SqlAlchemyRegistroForoVersionRepository(sesion)

        v1 = repo.guardar(
            RegistroForoVersion(
                persona_master_id=pm_id, clave_registro="registro:r1", numero_version=1, registro="R1",
                provincia="Pichincha", fecha_inicio=date(2026, 1, 1), consulta_foro_id=consulta_id,
            )
        )
        v1.cerrar(date(2026, 2, 1))
        repo.guardar(v1)
        repo.guardar(
            RegistroForoVersion(
                persona_master_id=pm_id, clave_registro="registro:r1", numero_version=2, registro="R1",
                provincia="Guayas", fecha_inicio=date(2026, 2, 1), consulta_foro_id=consulta_id,
            )
        )

        vigente = repo.buscar_vigente(pm_id, "registro:r1")
        assert vigente is not None
        assert vigente.numero_version == 2
        historial = repo.listar_historial(pm_id, "registro:r1")
        assert [v.numero_version for v in historial] == [1, 2]
        assert len(repo.listar_por_persona_master(pm_id)) == 2


class TestSqlAlchemyHistorialForoRepository:
    def test_guardar_lote_y_listar(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        consulta_id = _consulta(sesion, pm_id)
        repo = SqlAlchemyHistorialForoRepository(sesion)
        repo.guardar_lote(
            [
                HistorialForo(
                    persona_master_id=pm_id, clave_registro="registro:r1", tipo_cambio=TipoCambioForo.DATO_NUEVO,
                    detectado_en=_AHORA, consulta_foro_id=consulta_id,
                    campos_modificados=[{"campo": "registro", "valor_anterior": None, "valor_nuevo": "R1"}],
                )
            ]
        )
        assert len(repo.listar_por_persona_master(pm_id)) == 1
        assert len(repo.listar_todo()) >= 1


class TestSqlAlchemyEventoForoRepository:
    def test_guardar_lote_y_listar_pendientes(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        repo = SqlAlchemyEventoForoRepository(sesion)
        guardados = repo.guardar_lote(
            [EventoForo(tipo=TipoEventoForo.REGISTRO_NUEVO, persona_master_id=pm_id, payload={}, creado_en=_AHORA)]
        )
        assert len(guardados) == 1
        assert len(repo.listar_pendientes()) == 1
        assert len(repo.listar_por_persona_master(pm_id)) == 1

        evento = repo.buscar_por_id(guardados[0].id)
        assert evento is not None
        evento.consumir(_AHORA)
        repo.guardar(evento)
        assert repo.listar_pendientes() == []


class TestSqlAlchemyAlertaForoRepository:
    def test_guardar_lote_y_listar(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        repo = SqlAlchemyAlertaForoRepository(sesion)
        repo.guardar_lote(
            [
                AlertaForo(
                    persona_master_id=pm_id, tipo=TipoAlertaForo.REGISTRO_NUEVO, prioridad=NivelCriticidad.MEDIO,
                    descripcion="x", detectado_en=_AHORA,
                )
            ]
        )
        recuperadas = repo.listar_por_persona_master(pm_id)
        assert len(recuperadas) == 1
        assert repo.buscar_por_id(recuperadas[0].id) is not None
        assert len(repo.listar_pendientes()) == 1
