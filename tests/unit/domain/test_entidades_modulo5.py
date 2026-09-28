"""Tests: invariantes de las nuevas entidades de dominio del Modulo 5 --
VersionFuncionario, Alerta, Evento, Verificacion, AuditoriaComparacion,
OportunidadComercial."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest

from govdata.domain.entities.alerta import Alerta, EstadoAlerta, TipoAlerta
from govdata.domain.entities.auditoria_comparacion import AuditoriaComparacion
from govdata.domain.entities.evento import EstadoEvento, Evento, TipoEvento
from govdata.domain.entities.oportunidad_comercial import OportunidadComercial, TipoOportunidad
from govdata.domain.entities.verificacion import Verificacion
from govdata.domain.entities.version_funcionario import EstadoVersion, VersionFuncionario
from govdata.domain.exceptions.domain_exceptions import (
    AlertaInvalidaError,
    AuditoriaComparacionInvalidaError,
    EventoInvalidoError,
    OportunidadComercialInvalidaError,
    VerificacionInvalidaError,
    VersionFuncionarioInvalidaError,
)
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad


def _version(**overrides) -> VersionFuncionario:
    base = {
        "persona_id": 1, "entidad_id": 1, "numero_version": 1, "cargo": "Director Juridico",
        "dependencia": "Legal", "area": "juridica", "documento_id": 10, "fecha_inicio": date(2026, 6, 1),
    }
    base.update(overrides)
    return VersionFuncionario(**base)


class TestVersionFuncionario:
    def test_version_valida_queda_vigente(self) -> None:
        version = _version()
        assert version.estado == EstadoVersion.VIGENTE
        assert version.vigente is True

    def test_numero_version_menor_a_uno_lanza_error(self) -> None:
        with pytest.raises(VersionFuncionarioInvalidaError, match="numero_version"):
            _version(numero_version=0)

    def test_cargo_vacio_lanza_error(self) -> None:
        with pytest.raises(VersionFuncionarioInvalidaError, match="cargo"):
            _version(cargo="   ")

    def test_dependencia_vacia_lanza_error(self) -> None:
        with pytest.raises(VersionFuncionarioInvalidaError, match="dependencia"):
            _version(dependencia="")

    def test_fecha_fin_anterior_a_inicio_lanza_error(self) -> None:
        with pytest.raises(VersionFuncionarioInvalidaError, match="fecha_fin"):
            _version(fecha_fin=date(2026, 1, 1), estado=EstadoVersion.CERRADA)

    def test_vigente_con_fecha_fin_lanza_error(self) -> None:
        with pytest.raises(VersionFuncionarioInvalidaError, match="VIGENTE"):
            _version(fecha_fin=date(2026, 7, 1), estado=EstadoVersion.VIGENTE)

    def test_cerrada_sin_fecha_fin_lanza_error(self) -> None:
        with pytest.raises(VersionFuncionarioInvalidaError, match="CERRADA"):
            _version(estado=EstadoVersion.CERRADA)

    def test_cerrar_version_vigente(self) -> None:
        version = _version()
        version.cerrar(date(2026, 7, 1))
        assert version.estado == EstadoVersion.CERRADA
        assert version.fecha_fin == date(2026, 7, 1)

    def test_cerrar_version_ya_cerrada_lanza_error(self) -> None:
        version = _version()
        version.cerrar(date(2026, 7, 1))
        with pytest.raises(VersionFuncionarioInvalidaError, match="VIGENTE"):
            version.cerrar(date(2026, 8, 1))

    def test_cerrar_antes_de_fecha_inicio_lanza_error(self) -> None:
        version = _version()
        with pytest.raises(VersionFuncionarioInvalidaError, match="fecha_inicio"):
            version.cerrar(date(2026, 1, 1))


class TestAlerta:
    def test_alerta_valida(self) -> None:
        alerta = Alerta(
            entidad_id=1, tipo=TipoAlerta.NUEVO_DIRECTOR_JURIDICO,
            prioridad=NivelCriticidad.CRITICO,
            descripcion="Nuevo director", detectado_en=datetime.now(UTC),
        )
        assert alerta.estado == EstadoAlerta.PENDIENTE
        assert isinstance(alerta.id, uuid.UUID)

    def test_descripcion_vacia_lanza_error(self) -> None:
        with pytest.raises(AlertaInvalidaError):
            Alerta(
                entidad_id=1, tipo=TipoAlerta.CAMBIO_CORREO, prioridad=NivelCriticidad.MEDIO,
                descripcion="   ", detectado_en=datetime.now(UTC),
            )

    def test_marcar_enviada(self) -> None:
        alerta = Alerta(
            entidad_id=1, tipo=TipoAlerta.CAMBIO_CORREO, prioridad=NivelCriticidad.MEDIO,
            descripcion="x", detectado_en=datetime.now(UTC),
        )
        alerta.marcar_enviada()
        assert alerta.estado == EstadoAlerta.ENVIADA

    def test_marcar_enviada_dos_veces_lanza_error(self) -> None:
        alerta = Alerta(
            entidad_id=1, tipo=TipoAlerta.CAMBIO_CORREO, prioridad=NivelCriticidad.MEDIO,
            descripcion="x", detectado_en=datetime.now(UTC),
        )
        alerta.marcar_enviada()
        with pytest.raises(AlertaInvalidaError):
            alerta.marcar_enviada()

    def test_descartar(self) -> None:
        alerta = Alerta(
            entidad_id=1, tipo=TipoAlerta.CAMBIO_CORREO, prioridad=NivelCriticidad.MEDIO,
            descripcion="x", detectado_en=datetime.now(UTC),
        )
        alerta.descartar()
        assert alerta.estado == EstadoAlerta.DESCARTADA

    def test_descartar_ya_enviada_lanza_error(self) -> None:
        alerta = Alerta(
            entidad_id=1, tipo=TipoAlerta.CAMBIO_CORREO, prioridad=NivelCriticidad.MEDIO,
            descripcion="x", detectado_en=datetime.now(UTC),
        )
        alerta.marcar_enviada()
        with pytest.raises(AlertaInvalidaError):
            alerta.descartar()


class TestEvento:
    def test_evento_nace_pendiente(self) -> None:
        evento = Evento(
            tipo=TipoEvento.ALERTA, entidad_id=1, referencia_id=uuid.uuid4(), payload={"x": 1},
            creado_en=datetime.now(UTC),
        )
        assert evento.estado == EstadoEvento.PENDIENTE

    def test_consumir_transiciona_a_consumido(self) -> None:
        evento = Evento(
            tipo=TipoEvento.ALERTA, entidad_id=1, referencia_id=uuid.uuid4(), payload={},
            creado_en=datetime.now(UTC),
        )
        evento.consumir(datetime.now(UTC))
        assert evento.estado == EstadoEvento.CONSUMIDO

    def test_procesar_despues_de_consumir(self) -> None:
        evento = Evento(
            tipo=TipoEvento.ALERTA, entidad_id=1, referencia_id=uuid.uuid4(), payload={},
            creado_en=datetime.now(UTC),
        )
        evento.consumir(datetime.now(UTC))
        evento.procesar(datetime.now(UTC))
        assert evento.estado == EstadoEvento.PROCESADO

    def test_procesar_sin_consumir_primero_lanza_error(self) -> None:
        evento = Evento(
            tipo=TipoEvento.ALERTA, entidad_id=1, referencia_id=uuid.uuid4(), payload={},
            creado_en=datetime.now(UTC),
        )
        with pytest.raises(EventoInvalidoError):
            evento.procesar(datetime.now(UTC))

    def test_consumir_dos_veces_lanza_error(self) -> None:
        evento = Evento(
            tipo=TipoEvento.ALERTA, entidad_id=1, referencia_id=uuid.uuid4(), payload={},
            creado_en=datetime.now(UTC),
        )
        evento.consumir(datetime.now(UTC))
        with pytest.raises(EventoInvalidoError):
            evento.consumir(datetime.now(UTC))

    def test_procesado_no_puede_transicionar_mas(self) -> None:
        evento = Evento(
            tipo=TipoEvento.ALERTA, entidad_id=1, referencia_id=uuid.uuid4(), payload={},
            creado_en=datetime.now(UTC),
        )
        evento.consumir(datetime.now(UTC))
        evento.procesar(datetime.now(UTC))
        with pytest.raises(EventoInvalidoError):
            evento.procesar(datetime.now(UTC))


class TestVerificacion:
    def test_verificacion_valida(self) -> None:
        verificacion = Verificacion(entidad_id=1, hubo_cambio=False, motivo="hash_sin_cambios", verificado_en=datetime.now(UTC))
        assert verificacion.hubo_cambio is False

    def test_motivo_vacio_lanza_error(self) -> None:
        with pytest.raises(VerificacionInvalidaError):
            Verificacion(entidad_id=1, hubo_cambio=False, motivo="  ", verificado_en=datetime.now(UTC))


class TestAuditoriaComparacion:
    def test_auditoria_valida(self) -> None:
        auditoria = AuditoriaComparacion(
            entidad_id=1, documento_id=10, version_documento=1, ejecutado_por="sistema",
            iniciado_en=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
        )
        assert auditoria.finalizado_en is None

    def test_ejecutado_por_vacio_lanza_error(self) -> None:
        with pytest.raises(AuditoriaComparacionInvalidaError):
            AuditoriaComparacion(
                entidad_id=1, documento_id=10, version_documento=1, ejecutado_por="  ",
                iniciado_en=datetime.now(UTC),
            )

    def test_version_documento_invalida_lanza_error(self) -> None:
        with pytest.raises(AuditoriaComparacionInvalidaError):
            AuditoriaComparacion(
                entidad_id=1, documento_id=10, version_documento=0, ejecutado_por="sistema",
                iniciado_en=datetime.now(UTC),
            )

    def test_finalizar_calcula_duracion(self) -> None:
        inicio = datetime(2026, 7, 1, 10, 0, 0, tzinfo=UTC)
        fin = datetime(2026, 7, 1, 10, 0, 5, tzinfo=UTC)
        auditoria = AuditoriaComparacion(
            entidad_id=1, documento_id=10, version_documento=1, ejecutado_por="sistema", iniciado_en=inicio
        )
        auditoria.finalizar(fin, cambios_detectados=3)
        assert auditoria.duracion_segundos == 5.0
        assert auditoria.cambios_detectados == 3

    def test_marcar_error_agrega_mensaje(self) -> None:
        auditoria = AuditoriaComparacion(
            entidad_id=1, documento_id=10, version_documento=1, ejecutado_por="sistema",
            iniciado_en=datetime.now(UTC),
        )
        auditoria.marcar_error("fallo de red", datetime.now(UTC))
        assert "fallo de red" in auditoria.errores


class TestOportunidadComercial:
    def test_oportunidad_valida(self) -> None:
        oportunidad = OportunidadComercial(
            entidad_id=1, tipo=TipoOportunidad.NUEVO_PROCURADOR, descripcion="Nuevo procurador",
            detectado_en=datetime.now(UTC),
        )
        assert isinstance(oportunidad.id, uuid.UUID)

    def test_descripcion_vacia_lanza_error(self) -> None:
        with pytest.raises(OportunidadComercialInvalidaError):
            OportunidadComercial(
                entidad_id=1, tipo=TipoOportunidad.NUEVO_PROCURADOR, descripcion="   ",
                detectado_en=datetime.now(UTC),
            )
