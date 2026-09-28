"""Tests: invariantes de las entidades nuevas del Modulo 8."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from govdata.domain.entities.alerta_foro import AlertaForo
from govdata.domain.entities.consulta_foro import ConsultaForo
from govdata.domain.entities.evento_foro import EventoForo
from govdata.domain.entities.historial_foro import HistorialForo
from govdata.domain.entities.registro_foro import RegistroForo
from govdata.domain.entities.registro_foro_version import EstadoVersionForo, RegistroForoVersion
from govdata.domain.exceptions.domain_exceptions import (
    AlertaForoInvalidaError,
    ConsultaForoInvalidaError,
    EventoForoInvalidoError,
    HistorialForoInvalidoError,
    RegistroForoInvalidoError,
    RegistroForoVersionInvalidaError,
)
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_foro import TipoAlertaForo
from govdata.domain.value_objects.tipo_cambio_foro import TipoCambioForo
from govdata.domain.value_objects.tipo_evento_foro import TipoEventoForo

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)
_FECHA = date(2026, 1, 1)


class TestRegistroForo:
    def test_requiere_al_menos_un_dato_identificador(self) -> None:
        with pytest.raises(RegistroForoInvalidoError):
            RegistroForo(persona_master_id=1, clave_registro="r1")

    def test_registro_solo_basta(self) -> None:
        RegistroForo(persona_master_id=1, clave_registro="r1", registro="R1")

    def test_nivel_confianza_fuera_de_rango(self) -> None:
        with pytest.raises(RegistroForoInvalidoError):
            RegistroForo(persona_master_id=1, clave_registro="r1", registro="R1", nivel_confianza=150.0)

    def test_cerrar_marca_no_vigente(self) -> None:
        registro = RegistroForo(persona_master_id=1, clave_registro="r1", registro="R1")
        registro.cerrar()
        assert registro.vigente is False


class TestRegistroForoVersion:
    def test_fecha_fin_anterior_a_inicio_falla(self) -> None:
        with pytest.raises(RegistroForoVersionInvalidaError):
            RegistroForoVersion(
                persona_master_id=1, clave_registro="r1", numero_version=1, fecha_inicio=date(2026, 2, 1),
                consulta_foro_id=1, fecha_fin=date(2026, 1, 1), estado_version=EstadoVersionForo.CERRADA,
            )

    def test_vigente_no_puede_tener_fecha_fin(self) -> None:
        with pytest.raises(RegistroForoVersionInvalidaError):
            RegistroForoVersion(
                persona_master_id=1, clave_registro="r1", numero_version=1, fecha_inicio=_FECHA,
                consulta_foro_id=1, fecha_fin=_FECHA,
            )

    def test_cerrar_transiciona_a_cerrada(self) -> None:
        version = RegistroForoVersion(
            persona_master_id=1, clave_registro="r1", numero_version=1, fecha_inicio=_FECHA, consulta_foro_id=1
        )
        version.cerrar(date(2026, 2, 1))
        assert version.vigente is False
        assert version.estado_version == EstadoVersionForo.CERRADA

    def test_no_se_puede_cerrar_dos_veces(self) -> None:
        version = RegistroForoVersion(
            persona_master_id=1, clave_registro="r1", numero_version=1, fecha_inicio=_FECHA, consulta_foro_id=1
        )
        version.cerrar(date(2026, 2, 1))
        with pytest.raises(RegistroForoVersionInvalidaError):
            version.cerrar(date(2026, 3, 1))


class TestHistorialForo:
    def test_rechaza_sin_cambios(self) -> None:
        with pytest.raises(HistorialForoInvalidoError):
            HistorialForo(
                persona_master_id=1, clave_registro="r1", tipo_cambio=TipoCambioForo.SIN_CAMBIOS,
                detectado_en=_AHORA, consulta_foro_id=1,
            )


class TestConsultaForo:
    def test_finalizar_antes_de_iniciado_en_falla(self) -> None:
        consulta = ConsultaForo(persona_master_id=1, iniciado_en=_AHORA)
        with pytest.raises(ConsultaForoInvalidaError):
            consulta.finalizar(exito=True, cuando=datetime(2025, 1, 1, tzinfo=UTC), duracion_segundos=1.0)

    def test_finalizar_registra_todos_los_campos_de_auditoria(self) -> None:
        consulta = ConsultaForo(persona_master_id=1, iniciado_en=_AHORA)
        consulta.finalizar(
            exito=True, cuando=_AHORA, duracion_segundos=2.0, codigo_http=200, captcha_detectado=False,
            pagina_vacia=False,
        )
        assert consulta.exito is True
        assert consulta.codigo_http == 200

    def test_registrar_reintento_incrementa_contador(self) -> None:
        consulta = ConsultaForo(persona_master_id=1, iniciado_en=_AHORA)
        consulta.registrar_reintento()
        consulta.registrar_reintento()
        assert consulta.reintentos == 2


class TestEventoForo:
    def test_transicion_valida_pendiente_a_consumido(self) -> None:
        evento = EventoForo(tipo=TipoEventoForo.REGISTRO_NUEVO, persona_master_id=1, payload={}, creado_en=_AHORA)
        evento.consumir(_AHORA)
        assert evento.consumido_en == _AHORA

    def test_transicion_invalida_lanza_error(self) -> None:
        evento = EventoForo(tipo=TipoEventoForo.REGISTRO_NUEVO, persona_master_id=1, payload={}, creado_en=_AHORA)
        with pytest.raises(EventoForoInvalidoError):
            evento.procesar(_AHORA)


class TestAlertaForo:
    def test_descripcion_vacia_falla(self) -> None:
        with pytest.raises(AlertaForoInvalidaError):
            AlertaForo(
                persona_master_id=1, tipo=TipoAlertaForo.CAMBIO_ESTADO, prioridad=NivelCriticidad.ALTO,
                descripcion="   ", detectado_en=_AHORA,
            )

    def test_marcar_enviada_y_descartar(self) -> None:
        alerta = AlertaForo(
            persona_master_id=1, tipo=TipoAlertaForo.CAMBIO_ESTADO, prioridad=NivelCriticidad.ALTO,
            descripcion="x", detectado_en=_AHORA,
        )
        alerta.marcar_enviada()
        assert alerta.estado.value == "enviada"
        alerta.descartar()
        assert alerta.estado.value == "descartada"
