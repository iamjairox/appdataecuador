"""Tests de integracion de persistencia -- los 7 repositorios nuevos del
Modulo 6 (PersonaMaster, RegistroFuente, AtributoTrazable,
CasoRevisionIdentidad, ConsultaFuenteLog, EventoPerfil, AlertaPerfil)
contra SQLite real."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.domain.entities.alerta_perfil import AlertaPerfil
from govdata.domain.entities.atributo_trazable import AtributoTrazable
from govdata.domain.entities.caso_revision_identidad import CasoRevisionIdentidad
from govdata.domain.entities.consulta_fuente_log import ConsultaFuenteLog
from govdata.domain.entities.evento_perfil import EventoPerfil
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.entities.registro_fuente import RegistroFuente
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.estado_revision_identidad import EstadoRevisionIdentidad
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.tipo_alerta_perfil import TipoAlertaPerfil
from govdata.domain.value_objects.tipo_evento_identidad import TipoEventoIdentidad
from govdata.infrastructure.persistence.postgresql.models.persona_model import PersonaModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_perfil_repository import (
    SqlAlchemyAlertaPerfilRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_atributo_trazable_repository import (
    SqlAlchemyAtributoTrazableRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_caso_revision_identidad_repository import (
    SqlAlchemyCasoRevisionIdentidadRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_consulta_fuente_log_repository import (
    SqlAlchemyConsultaFuenteLogRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_perfil_repository import (
    SqlAlchemyEventoPerfilRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_persona_master_repository import (
    SqlAlchemyPersonaMasterRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_registro_fuente_repository import (
    SqlAlchemyRegistroFuenteRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def _persona(sesion, nombres: str = "Juan") -> int:
    modelo = PersonaModel(nombres=nombres, apellidos="Perez")
    sesion.add(modelo)
    sesion.flush()
    return modelo.id


def _persona_master(sesion, persona_id: int, fingerprint: str = "JUANPEREZ") -> PersonaMaster:
    repo = SqlAlchemyPersonaMasterRepository(sesion)
    return repo.guardar(
        PersonaMaster(
            persona_id=persona_id, nombre_completo=NombreCompleto("Juan", "Perez"), fingerprint_principal=fingerprint,
            correo_principal=Correo("juan@x.com"),
        )
    )


class TestSqlAlchemyPersonaMasterRepository:
    def test_guardar_y_recuperar_por_id(self, sesion) -> None:
        persona_id = _persona(sesion)
        pm = _persona_master(sesion, persona_id)
        recuperado = SqlAlchemyPersonaMasterRepository(sesion).buscar_por_id(pm.id)
        assert recuperado is not None
        assert recuperado.persona_id == persona_id
        assert str(recuperado.correo_principal) == "juan@x.com"

    def test_buscar_por_persona_id_es_idempotente(self, sesion) -> None:
        persona_id = _persona(sesion)
        pm1 = _persona_master(sesion, persona_id)
        repo = SqlAlchemyPersonaMasterRepository(sesion)
        encontrado = repo.buscar_por_persona_id(persona_id)
        assert encontrado is not None
        assert encontrado.id == pm1.id

    def test_buscar_por_fingerprint_principal(self, sesion) -> None:
        persona_id = _persona(sesion)
        _persona_master(sesion, persona_id, fingerprint="UNICOFP")
        repo = SqlAlchemyPersonaMasterRepository(sesion)
        assert repo.buscar_por_fingerprint_principal("UNICOFP") is not None
        assert repo.buscar_por_fingerprint_principal("NOEXISTE") is None

    def test_buscar_candidatas_por_correo(self, sesion) -> None:
        persona_id = _persona(sesion)
        _persona_master(sesion, persona_id)
        repo = SqlAlchemyPersonaMasterRepository(sesion)
        candidatas = repo.buscar_candidatas_por_correo("juan@x.com")
        assert len(candidatas) == 1

    def test_listar_activas_excluye_fusionadas(self, sesion) -> None:
        persona_id_1 = _persona(sesion, "Juan")
        persona_id_2 = _persona(sesion, "Maria")
        pm1 = _persona_master(sesion, persona_id_1, fingerprint="FP1")
        pm2 = _persona_master(sesion, persona_id_2, fingerprint="FP2")
        pm2.fusionar_en(pm1.id)
        repo = SqlAlchemyPersonaMasterRepository(sesion)
        repo.guardar(pm2)

        activas = repo.listar_activas(limite=10)
        assert pm2.id not in [p.id for p in activas]
        assert repo.contar_activas() == 1


class TestSqlAlchemyRegistroFuenteRepository:
    def test_versionado_nunca_sobreescribe(self, sesion) -> None:
        persona_id = _persona(sesion)
        pm = _persona_master(sesion, persona_id)
        repo = SqlAlchemyRegistroFuenteRepository(sesion)

        v1 = repo.guardar(
            RegistroFuente(persona_master_id=pm.id, fuente=FuenteExterna.SENESCYT, version=1, datos={"titulo": "Abogado"})
        )
        v1.cerrar()
        repo.guardar(v1)
        v2 = repo.guardar(
            RegistroFuente(
                persona_master_id=pm.id, fuente=FuenteExterna.SENESCYT, version=2,
                datos={"titulo": "Doctor en Jurisprudencia"},
            )
        )

        vigente = repo.buscar_vigente(pm.id, FuenteExterna.SENESCYT)
        assert vigente is not None and vigente.id == v2.id
        historial = repo.listar_historial(pm.id, FuenteExterna.SENESCYT)
        assert [r.version for r in historial] == [1, 2]


class TestSqlAlchemyAtributoTrazableRepository:
    def test_guardar_lote_y_listar(self, sesion) -> None:
        persona_id = _persona(sesion)
        pm = _persona_master(sesion, persona_id)
        repo = SqlAlchemyAtributoTrazableRepository(sesion)
        repo.guardar_lote(
            [
                AtributoTrazable(
                    persona_master_id=pm.id, campo="titulo", valor="Abogado", fuente=FuenteExterna.SENESCYT,
                    obtenido_en=_AHORA, score=90.0,
                )
            ]
        )
        assert len(repo.listar_por_persona_master(pm.id)) == 1


class TestSqlAlchemyCasoRevisionIdentidadRepository:
    def test_guardar_y_listar_pendientes(self, sesion) -> None:
        persona_id_1 = _persona(sesion, "Juan")
        persona_id_2 = _persona(sesion, "Juan Carlos")
        pm1 = _persona_master(sesion, persona_id_1, fingerprint="FP1")
        pm2 = _persona_master(sesion, persona_id_2, fingerprint="FP2")
        repo = SqlAlchemyCasoRevisionIdentidadRepository(sesion)

        caso = repo.guardar(
            CasoRevisionIdentidad(
                persona_master_id_a=pm1.id, persona_master_id_b=pm2.id, score=90.0, explicacion="x",
                campos_utilizados=("correo",), creado_en=_AHORA,
            )
        )
        assert repo.buscar_por_id(caso.uuid) is not None
        assert len(repo.listar_pendientes()) == 1
        assert repo.buscar_pendiente_entre(pm1.id, pm2.id) is not None
        assert repo.buscar_pendiente_entre(pm2.id, pm1.id) is not None  # simetrico

    def test_caso_resuelto_ya_no_aparece_como_pendiente(self, sesion) -> None:
        persona_id_1 = _persona(sesion, "Juan")
        persona_id_2 = _persona(sesion, "Juan Carlos")
        pm1 = _persona_master(sesion, persona_id_1, fingerprint="FP1")
        pm2 = _persona_master(sesion, persona_id_2, fingerprint="FP2")
        repo = SqlAlchemyCasoRevisionIdentidadRepository(sesion)

        caso = CasoRevisionIdentidad(
            persona_master_id_a=pm1.id, persona_master_id_b=pm2.id, score=90.0, explicacion="x",
            campos_utilizados=(), creado_en=_AHORA,
        )
        caso.aprobar("ana.revisora", _AHORA)
        repo.guardar(caso)

        assert repo.listar_pendientes() == []
        assert repo.buscar_pendiente_entre(pm1.id, pm2.id) is None
        recuperado = repo.buscar_por_id(caso.uuid)
        assert recuperado is not None
        assert recuperado.estado == EstadoRevisionIdentidad.APROBADO
        assert recuperado.resuelto_por == "ana.revisora"


class TestSqlAlchemyConsultaFuenteLogRepository:
    def test_ultima_consulta_ordena_por_iniciado_en(self, sesion) -> None:
        persona_id = _persona(sesion)
        pm = _persona_master(sesion, persona_id)
        repo = SqlAlchemyConsultaFuenteLogRepository(sesion)

        log1 = ConsultaFuenteLog(persona_master_id=pm.id, fuente=FuenteExterna.SRI, iniciado_en=datetime(2026, 1, 1, tzinfo=UTC))
        log1.finalizar(exito=True, cuando=datetime(2026, 1, 1, tzinfo=UTC), duracion_segundos=1.0)
        repo.guardar(log1)
        log2 = ConsultaFuenteLog(persona_master_id=pm.id, fuente=FuenteExterna.SRI, iniciado_en=datetime(2026, 2, 1, tzinfo=UTC))
        log2.finalizar(exito=True, cuando=datetime(2026, 2, 1, tzinfo=UTC), duracion_segundos=1.0)
        repo.guardar(log2)

        ultima = repo.ultima_consulta(pm.id, FuenteExterna.SRI)
        assert ultima is not None
        # SQLite no preserva tzinfo en el redondeo (a diferencia de Postgres real);
        # se compara solo el valor naive, consistente con el resto de la suite.
        assert ultima.iniciado_en.replace(tzinfo=UTC) == datetime(2026, 2, 1, tzinfo=UTC)
        assert len(repo.listar_por_persona_master(pm.id)) == 2


class TestSqlAlchemyEventoPerfilRepository:
    def test_guardar_lote_y_listar_pendientes(self, sesion) -> None:
        persona_id = _persona(sesion)
        pm = _persona_master(sesion, persona_id)
        repo = SqlAlchemyEventoPerfilRepository(sesion)
        eventos = [
            EventoPerfil(tipo=TipoEventoIdentidad.NUEVA_FUENTE, persona_master_id=pm.id, payload={"fuente": "senescyt"}, creado_en=_AHORA)
        ]
        guardados = repo.guardar_lote(eventos)
        assert len(guardados) == 1
        assert len(repo.listar_pendientes()) == 1
        assert len(repo.listar_por_persona_master(pm.id)) == 1

        evento = repo.buscar_por_id(guardados[0].id)
        assert evento is not None
        evento.consumir(_AHORA)
        repo.guardar(evento)
        assert repo.listar_pendientes() == []


class TestSqlAlchemyAlertaPerfilRepository:
    def test_guardar_lote_y_listar_por_persona_master(self, sesion) -> None:
        persona_id = _persona(sesion)
        pm = _persona_master(sesion, persona_id)
        repo = SqlAlchemyAlertaPerfilRepository(sesion)
        alertas = [
            AlertaPerfil(
                persona_master_id=pm.id, tipo=TipoAlertaPerfil.TITULO_CAMBIADO, prioridad=NivelCriticidad.MEDIO,
                descripcion="x", detectado_en=_AHORA,
            )
        ]
        repo.guardar_lote(alertas)
        recuperadas = repo.listar_por_persona_master(pm.id)
        assert len(recuperadas) == 1
        assert repo.buscar_por_id(recuperadas[0].id) is not None
