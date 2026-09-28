"""Tests de integracion de persistencia -- los 6 repositorios nuevos del
Modulo 5 (VersionFuncionario, Alerta, Evento, Verificacion,
AuditoriaComparacion, OportunidadComercial) contra SQLite real."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from govdata.domain.entities.alerta import Alerta, EstadoAlerta, TipoAlerta
from govdata.domain.entities.auditoria_comparacion import AuditoriaComparacion
from govdata.domain.entities.evento import Evento, TipoEvento
from govdata.domain.entities.oportunidad_comercial import OportunidadComercial, TipoOportunidad
from govdata.domain.entities.verificacion import Verificacion
from govdata.domain.entities.version_funcionario import VersionFuncionario
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.infrastructure.persistence.postgresql.models.documento_model import DocumentoModel
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel
from govdata.infrastructure.persistence.postgresql.models.persona_model import PersonaModel
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_repository import (
    SqlAlchemyAlertaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_auditoria_comparacion_repository import (
    SqlAlchemyAuditoriaComparacionRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_evento_repository import (
    SqlAlchemyEventoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_oportunidad_comercial_repository import (
    SqlAlchemyOportunidadComercialRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_verificacion_repository import (
    SqlAlchemyVerificacionRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_version_funcionario_repository import (
    SqlAlchemyVersionFuncionarioRepository,
)


def _entidad(sesion, nombre: str = "Entidad X") -> int:
    modelo = EntidadModel(nombre=nombre, url_transparencia=f"https://x/{nombre}", portal_origen="dpe")
    sesion.add(modelo)
    sesion.flush()
    return modelo.id


def _persona(sesion, nombres: str = "Juan") -> int:
    modelo = PersonaModel(nombres=nombres, apellidos="Perez")
    sesion.add(modelo)
    sesion.flush()
    return modelo.id


def _documento(sesion, publicacion_id: int = 1) -> int:
    modelo = DocumentoModel(
        publicacion_id=publicacion_id, tipo_archivo="pdf", nombre_original="d.pdf",
        url_documento=f"https://x/d{publicacion_id}.pdf", estado="descargado",
        hash_sha256="a" * 64, tamano_bytes=10, ruta_almacenamiento="file:///a", version=1,
    )
    sesion.add(modelo)
    sesion.flush()
    return modelo.id


class TestSqlAlchemyVersionFuncionarioRepository:
    def test_guardar_y_buscar_vigente(self, sesion) -> None:
        entidad_id = _entidad(sesion)
        persona_id = _persona(sesion)
        documento_id = _documento(sesion)
        repo = SqlAlchemyVersionFuncionarioRepository(sesion)

        version = repo.guardar(
            VersionFuncionario(
                persona_id=persona_id, entidad_id=entidad_id, numero_version=1, cargo="Director Juridico",
                dependencia="Legal", area="juridica", documento_id=documento_id, fecha_inicio=date(2026, 6, 1),
            )
        )
        sesion.flush()

        vigente = repo.buscar_vigente(persona_id, entidad_id)
        assert vigente is not None
        assert vigente.id == version.id

    def test_cerrar_y_abrir_siguiente_version(self, sesion) -> None:
        entidad_id = _entidad(sesion)
        persona_id = _persona(sesion)
        documento_id = _documento(sesion)
        repo = SqlAlchemyVersionFuncionarioRepository(sesion)

        v1 = repo.guardar(
            VersionFuncionario(
                persona_id=persona_id, entidad_id=entidad_id, numero_version=1, cargo="Asesor Juridico",
                dependencia="Legal", area="juridica", documento_id=documento_id, fecha_inicio=date(2026, 6, 1),
            )
        )
        v1.cerrar(date(2026, 7, 1))
        repo.guardar(v1)

        documento_id_2 = _documento(sesion, publicacion_id=2)
        repo.guardar(
            VersionFuncionario(
                persona_id=persona_id, entidad_id=entidad_id, numero_version=2, cargo="Director Juridico",
                dependencia="Legal", area="juridica", documento_id=documento_id_2, fecha_inicio=date(2026, 7, 1),
            )
        )
        sesion.flush()

        vigente = repo.buscar_vigente(persona_id, entidad_id)
        assert vigente.numero_version == 2
        historial = repo.listar_por_persona(persona_id)
        assert len(historial) == 2

    def test_buscar_vigente_en_fecha(self, sesion) -> None:
        entidad_id = _entidad(sesion)
        persona_id = _persona(sesion)
        documento_id = _documento(sesion)
        repo = SqlAlchemyVersionFuncionarioRepository(sesion)
        version = repo.guardar(
            VersionFuncionario(
                persona_id=persona_id, entidad_id=entidad_id, numero_version=1, cargo="Director Juridico",
                dependencia="Legal", area="juridica", documento_id=documento_id, fecha_inicio=date(2026, 6, 1),
            )
        )
        sesion.flush()

        encontrada = repo.buscar_vigente_en_fecha(entidad_id, "Director Juridico", date(2026, 6, 15))
        assert encontrada is not None
        assert encontrada.id == version.id

        no_encontrada = repo.buscar_vigente_en_fecha(entidad_id, "Director Juridico", date(2026, 1, 1))
        assert no_encontrada is None

    def test_listar_por_entidad_y_cargo(self, sesion) -> None:
        entidad_id = _entidad(sesion)
        persona_id = _persona(sesion)
        documento_id = _documento(sesion)
        repo = SqlAlchemyVersionFuncionarioRepository(sesion)
        repo.guardar(
            VersionFuncionario(
                persona_id=persona_id, entidad_id=entidad_id, numero_version=1, cargo="Director Juridico",
                dependencia="Legal", area="juridica", documento_id=documento_id, fecha_inicio=date(2026, 6, 1),
            )
        )
        sesion.flush()
        resultado = repo.listar_por_entidad_y_cargo(entidad_id, "Director Juridico")
        assert len(resultado) == 1


class TestSqlAlchemyAlertaRepository:
    def test_guardar_y_listar_por_entidad_y_documento(self, sesion) -> None:
        entidad_id = _entidad(sesion)
        documento_id = _documento(sesion)
        repo = SqlAlchemyAlertaRepository(sesion)
        alerta = repo.guardar(
            Alerta(
                entidad_id=entidad_id, tipo=TipoAlerta.NUEVO_DIRECTOR_JURIDICO, prioridad=NivelCriticidad.CRITICO,
                descripcion="x", detectado_en=datetime.now(UTC), documento_id=documento_id,
            )
        )
        sesion.flush()

        recuperada = repo.buscar_por_id(alerta.id)
        assert recuperada is not None
        assert recuperada.estado == EstadoAlerta.PENDIENTE
        assert len(repo.listar_por_entidad(entidad_id)) == 1
        assert len(repo.listar_por_documento(documento_id)) == 1

    def test_guardar_lote(self, sesion) -> None:
        entidad_id = _entidad(sesion)
        repo = SqlAlchemyAlertaRepository(sesion)
        alertas = [
            Alerta(entidad_id=entidad_id, tipo=TipoAlerta.CAMBIO_CORREO, prioridad=NivelCriticidad.MEDIO, descripcion="a", detectado_en=datetime.now(UTC)),
            Alerta(entidad_id=entidad_id, tipo=TipoAlerta.CAMBIO_CARGO, prioridad=NivelCriticidad.MEDIO, descripcion="b", detectado_en=datetime.now(UTC)),
        ]
        repo.guardar_lote(alertas)
        sesion.flush()
        assert len(repo.listar_por_entidad(entidad_id)) == 2


class TestSqlAlchemyEventoRepository:
    def test_guardar_y_listar_pendientes(self, sesion) -> None:
        entidad_id = _entidad(sesion)
        repo = SqlAlchemyEventoRepository(sesion)
        evento = repo.guardar(
            Evento(tipo=TipoEvento.ALERTA, entidad_id=entidad_id, referencia_id=uuid.uuid4(), payload={"x": 1}, creado_en=datetime.now(UTC))
        )
        sesion.flush()

        pendientes = repo.listar_pendientes(10)
        assert len(pendientes) == 1
        assert pendientes[0].id == evento.id

    def test_consumir_y_procesar_persisten_la_transicion(self, sesion) -> None:
        entidad_id = _entidad(sesion)
        repo = SqlAlchemyEventoRepository(sesion)
        evento = repo.guardar(
            Evento(tipo=TipoEvento.ALERTA, entidad_id=entidad_id, referencia_id=uuid.uuid4(), payload={}, creado_en=datetime.now(UTC))
        )
        sesion.flush()

        evento.consumir(datetime.now(UTC))
        repo.guardar(evento)
        sesion.flush()

        recuperado = repo.buscar_por_id(evento.id)
        from govdata.domain.entities.evento import EstadoEvento

        assert recuperado.estado == EstadoEvento.CONSUMIDO
        assert repo.listar_pendientes(10) == []


class TestSqlAlchemyVerificacionRepository:
    def test_registrar_y_buscar_ultima(self, sesion) -> None:
        entidad_id = _entidad(sesion)
        repo = SqlAlchemyVerificacionRepository(sesion)
        repo.registrar(Verificacion(entidad_id=entidad_id, hubo_cambio=False, motivo="primera", verificado_en=datetime(2026, 6, 1, tzinfo=UTC)))
        repo.registrar(Verificacion(entidad_id=entidad_id, hubo_cambio=True, motivo="segunda", verificado_en=datetime(2026, 7, 1, tzinfo=UTC)))
        sesion.flush()

        ultima = repo.buscar_ultima_por_entidad(entidad_id)
        assert ultima.motivo == "segunda"
        assert len(repo.listar_por_entidad(entidad_id)) == 2


class TestSqlAlchemyAuditoriaComparacionRepository:
    def test_registrar_iniciar_y_finalizar(self, sesion) -> None:
        entidad_id = _entidad(sesion)
        documento_id = _documento(sesion)
        repo = SqlAlchemyAuditoriaComparacionRepository(sesion)
        auditoria = repo.registrar(
            AuditoriaComparacion(entidad_id=entidad_id, documento_id=documento_id, version_documento=1, ejecutado_por="sistema", iniciado_en=datetime.now(UTC))
        )
        sesion.flush()

        auditoria.finalizar(datetime.now(UTC), cambios_detectados=3)
        repo.registrar(auditoria)
        sesion.flush()

        listadas = repo.listar_por_documento(documento_id)
        assert len(listadas) == 1
        assert listadas[0].cambios_detectados == 3
        assert listadas[0].finalizado_en is not None


class TestSqlAlchemyOportunidadComercialRepository:
    def test_guardar_y_listar_por_entidad(self, sesion) -> None:
        entidad_id = _entidad(sesion)
        persona_id = _persona(sesion)
        repo = SqlAlchemyOportunidadComercialRepository(sesion)
        repo.guardar(
            OportunidadComercial(
                entidad_id=entidad_id, tipo=TipoOportunidad.NUEVO_PROCURADOR, descripcion="x",
                detectado_en=datetime.now(UTC), persona_id=persona_id, prioridad=NivelCriticidad.CRITICO,
            )
        )
        sesion.flush()
        assert len(repo.listar_por_entidad(entidad_id)) == 1
