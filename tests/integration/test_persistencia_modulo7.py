"""Tests de integracion de persistencia -- los 6 repositorios nuevos del
Modulo 7 (TituloAcademico, TituloVersionAcademica, HistorialAcademico,
ConsultaSenescyt, EventoAcademico, AlertaAcademica) contra SQLite real."""

from __future__ import annotations

from datetime import UTC, date, datetime

from govdata.domain.entities.alerta_academica import AlertaAcademica
from govdata.domain.entities.consulta_senescyt import ConsultaSenescyt
from govdata.domain.entities.evento_academico import EventoAcademico
from govdata.domain.entities.historial_academico import HistorialAcademico
from govdata.domain.entities.titulo_academico import TituloAcademico
from govdata.domain.entities.titulo_version_academica import TituloVersionAcademica
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_academica import TipoAlertaAcademica
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico
from govdata.domain.value_objects.tipo_evento_academico import TipoEventoAcademico
from govdata.infrastructure.persistence.postgresql.models.persona_model import PersonaModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_academica_repository import (
    SqlAlchemyAlertaAcademicaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_consulta_senescyt_repository import (
    SqlAlchemyConsultaSenescytRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_academico_repository import (
    SqlAlchemyEventoAcademicoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_historial_academico_repository import (
    SqlAlchemyHistorialAcademicoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_titulo_academico_repository import (
    SqlAlchemyTituloAcademicoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_titulo_version_academica_repository import (
    SqlAlchemyTituloVersionAcademicaRepository,
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
    repo = SqlAlchemyConsultaSenescytRepository(sesion)
    consulta = repo.guardar(ConsultaSenescyt(persona_master_id=persona_master_id, iniciado_en=_AHORA))
    return consulta.id


class TestSqlAlchemyConsultaSenescytRepository:
    def test_guardar_finalizar_y_recuperar(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        repo = SqlAlchemyConsultaSenescytRepository(sesion)
        consulta = repo.guardar(ConsultaSenescyt(persona_master_id=pm_id, iniciado_en=_AHORA))
        consulta.finalizar(exito=True, cuando=_AHORA, duracion_segundos=2.0, respuesta_cruda={"titulos": []})
        repo.guardar(consulta)

        ultima = repo.ultima_consulta(pm_id)
        assert ultima is not None
        assert ultima.exito is True
        assert ultima.respuesta_cruda == {"titulos": []}
        assert len(repo.listar_por_persona_master(pm_id)) == 1
        assert len(repo.listar_todas()) >= 1


class TestSqlAlchemyTituloAcademicoRepository:
    def test_guardar_y_buscar_vigente(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        consulta_id = _consulta(sesion, pm_id)
        repo = SqlAlchemyTituloAcademicoRepository(sesion)
        repo.guardar(
            TituloAcademico(
                persona_master_id=pm_id, clave_titulo="registro:r1", titulo="ABOGADO", nivel="TERCER NIVEL",
                institucion="UCE", evidencia=str(consulta_id),
            )
        )
        vigente = repo.buscar_vigente_por_clave(pm_id, "registro:r1")
        assert vigente is not None
        assert len(repo.listar_vigentes_por_persona_master(pm_id)) == 1

    def test_titulo_no_vigente_no_aparece_en_listado(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        repo = SqlAlchemyTituloAcademicoRepository(sesion)
        titulo = repo.guardar(
            TituloAcademico(
                persona_master_id=pm_id, clave_titulo="registro:r1", titulo="ABOGADO", nivel="TERCER NIVEL",
                institucion="UCE",
            )
        )
        titulo.cerrar()
        repo.guardar(titulo)
        assert repo.listar_vigentes_por_persona_master(pm_id) == []
        assert repo.buscar_vigente_por_clave(pm_id, "registro:r1") is None


class TestSqlAlchemyTituloVersionAcademicaRepository:
    def test_versionado_nunca_sobreescribe(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        consulta_id = _consulta(sesion, pm_id)
        repo = SqlAlchemyTituloVersionAcademicaRepository(sesion)

        v1 = repo.guardar(
            TituloVersionAcademica(
                persona_master_id=pm_id, clave_titulo="registro:r1", numero_version=1, titulo="ABOGADO",
                nivel="TERCER NIVEL", institucion="UCE", fecha_inicio=date(2026, 1, 1), consulta_senescyt_id=consulta_id,
            )
        )
        v1.cerrar(date(2026, 2, 1))
        repo.guardar(v1)
        repo.guardar(
            TituloVersionAcademica(
                persona_master_id=pm_id, clave_titulo="registro:r1", numero_version=2,
                titulo="ABOGADO", nivel="CUARTO NIVEL", institucion="UCE", fecha_inicio=date(2026, 2, 1),
                consulta_senescyt_id=consulta_id,
            )
        )

        vigente = repo.buscar_vigente(pm_id, "registro:r1")
        assert vigente is not None
        assert vigente.numero_version == 2
        historial = repo.listar_historial(pm_id, "registro:r1")
        assert [v.numero_version for v in historial] == [1, 2]
        assert len(repo.listar_por_persona_master(pm_id)) == 2


class TestSqlAlchemyHistorialAcademicoRepository:
    def test_guardar_lote_y_listar(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        consulta_id = _consulta(sesion, pm_id)
        repo = SqlAlchemyHistorialAcademicoRepository(sesion)
        repo.guardar_lote(
            [
                HistorialAcademico(
                    persona_master_id=pm_id, clave_titulo="registro:r1", tipo_cambio=TipoCambioAcademico.TITULO_NUEVO,
                    detectado_en=_AHORA, consulta_senescyt_id=consulta_id,
                    campos_modificados=[{"campo": "titulo", "valor_anterior": None, "valor_nuevo": "ABOGADO"}],
                )
            ]
        )
        assert len(repo.listar_por_persona_master(pm_id)) == 1
        assert len(repo.listar_todo()) >= 1


class TestSqlAlchemyEventoAcademicoRepository:
    def test_guardar_lote_y_listar_pendientes(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        repo = SqlAlchemyEventoAcademicoRepository(sesion)
        guardados = repo.guardar_lote(
            [EventoAcademico(tipo=TipoEventoAcademico.TITULO_NUEVO, persona_master_id=pm_id, payload={}, creado_en=_AHORA)]
        )
        assert len(guardados) == 1
        assert len(repo.listar_pendientes()) == 1
        assert len(repo.listar_por_persona_master(pm_id)) == 1

        evento = repo.buscar_por_id(guardados[0].id)
        assert evento is not None
        evento.consumir(_AHORA)
        repo.guardar(evento)
        assert repo.listar_pendientes() == []


class TestSqlAlchemyAlertaAcademicaRepository:
    def test_guardar_lote_y_listar(self, sesion) -> None:
        pm_id = _persona_master_id(sesion)
        repo = SqlAlchemyAlertaAcademicaRepository(sesion)
        repo.guardar_lote(
            [
                AlertaAcademica(
                    persona_master_id=pm_id, tipo=TipoAlertaAcademica.NUEVO_TITULO, prioridad=NivelCriticidad.MEDIO,
                    descripcion="x", detectado_en=_AHORA,
                )
            ]
        )
        recuperadas = repo.listar_por_persona_master(pm_id)
        assert len(recuperadas) == 1
        assert repo.buscar_por_id(recuperadas[0].id) is not None
        assert len(repo.listar_pendientes()) == 1
