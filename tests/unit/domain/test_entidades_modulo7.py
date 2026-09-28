"""Tests: invariantes de las 6 nuevas entidades de dominio del Modulo 7."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from govdata.domain.entities.alerta_academica import AlertaAcademica
from govdata.domain.entities.consulta_senescyt import ConsultaSenescyt
from govdata.domain.entities.evento_academico import EventoAcademico
from govdata.domain.entities.historial_academico import HistorialAcademico
from govdata.domain.entities.titulo_academico import TituloAcademico
from govdata.domain.entities.titulo_version_academica import (
    EstadoVersionAcademica,
    TituloVersionAcademica,
)
from govdata.domain.exceptions.domain_exceptions import (
    AlertaAcademicaInvalidaError,
    ConsultaSenescytInvalidaError,
    EventoAcademicoInvalidoError,
    HistorialAcademicoInvalidoError,
    TituloAcademicoInvalidoError,
    TituloVersionAcademicaInvalidaError,
)
from govdata.domain.value_objects.estado_alerta_academica import EstadoAlertaAcademica
from govdata.domain.value_objects.estado_registro_academico import EstadoRegistroAcademico
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_academica import TipoAlertaAcademica
from govdata.domain.value_objects.tipo_cambio_academico import TipoCambioAcademico
from govdata.domain.value_objects.tipo_evento_academico import TipoEventoAcademico

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestTituloAcademico:
    def test_construccion_valida(self) -> None:
        titulo = TituloAcademico(persona_master_id=1, clave_titulo="x", titulo="Abogado", nivel="Tercer Nivel", institucion="UCE")
        assert titulo.vigente

    def test_titulo_vacio_falla(self) -> None:
        with pytest.raises(TituloAcademicoInvalidoError):
            TituloAcademico(persona_master_id=1, clave_titulo="x", titulo="  ", nivel="Tercer Nivel", institucion="UCE")

    def test_institucion_vacia_falla(self) -> None:
        with pytest.raises(TituloAcademicoInvalidoError):
            TituloAcademico(persona_master_id=1, clave_titulo="x", titulo="Abogado", nivel="Tercer Nivel", institucion=" ")

    def test_nivel_confianza_fuera_de_rango_falla(self) -> None:
        with pytest.raises(TituloAcademicoInvalidoError):
            TituloAcademico(
                persona_master_id=1, clave_titulo="x", titulo="Abogado", nivel="Tercer Nivel", institucion="UCE",
                nivel_confianza=150.0,
            )

    def test_numero_version_invalida_falla(self) -> None:
        with pytest.raises(TituloAcademicoInvalidoError):
            TituloAcademico(
                persona_master_id=1, clave_titulo="x", titulo="Abogado", nivel="Tercer Nivel", institucion="UCE",
                numero_version=0,
            )

    def test_cerrar_marca_no_vigente(self) -> None:
        titulo = TituloAcademico(persona_master_id=1, clave_titulo="x", titulo="Abogado", nivel="Tercer Nivel", institucion="UCE")
        titulo.cerrar()
        assert not titulo.vigente


class TestTituloVersionAcademica:
    def test_construccion_valida(self) -> None:
        version = TituloVersionAcademica(
            persona_master_id=1, clave_titulo="x", numero_version=1, titulo="Abogado", nivel="Tercer Nivel",
            institucion="UCE", fecha_inicio=date(2026, 1, 1), consulta_senescyt_id=1,
        )
        assert version.vigente

    def test_numero_version_invalida_falla(self) -> None:
        with pytest.raises(TituloVersionAcademicaInvalidaError):
            TituloVersionAcademica(
                persona_master_id=1, clave_titulo="x", numero_version=0, titulo="Abogado", nivel="Tercer Nivel",
                institucion="UCE", fecha_inicio=date(2026, 1, 1), consulta_senescyt_id=1,
            )

    def test_vigente_con_fecha_fin_falla(self) -> None:
        with pytest.raises(TituloVersionAcademicaInvalidaError):
            TituloVersionAcademica(
                persona_master_id=1, clave_titulo="x", numero_version=1, titulo="Abogado", nivel="Tercer Nivel",
                institucion="UCE", fecha_inicio=date(2026, 1, 1), consulta_senescyt_id=1, fecha_fin=date(2026, 2, 1),
            )

    def test_cerrada_sin_fecha_fin_falla(self) -> None:
        with pytest.raises(TituloVersionAcademicaInvalidaError):
            TituloVersionAcademica(
                persona_master_id=1, clave_titulo="x", numero_version=1, titulo="Abogado", nivel="Tercer Nivel",
                institucion="UCE", fecha_inicio=date(2026, 1, 1), consulta_senescyt_id=1,
                estado_version=EstadoVersionAcademica.CERRADA,
            )

    def test_cerrar_antes_de_fecha_inicio_falla(self) -> None:
        version = TituloVersionAcademica(
            persona_master_id=1, clave_titulo="x", numero_version=1, titulo="Abogado", nivel="Tercer Nivel",
            institucion="UCE", fecha_inicio=date(2026, 2, 1), consulta_senescyt_id=1,
        )
        with pytest.raises(TituloVersionAcademicaInvalidaError):
            version.cerrar(date(2026, 1, 1))

    def test_cerrar_dos_veces_falla(self) -> None:
        version = TituloVersionAcademica(
            persona_master_id=1, clave_titulo="x", numero_version=1, titulo="Abogado", nivel="Tercer Nivel",
            institucion="UCE", fecha_inicio=date(2026, 1, 1), consulta_senescyt_id=1,
        )
        version.cerrar(date(2026, 2, 1))
        with pytest.raises(TituloVersionAcademicaInvalidaError):
            version.cerrar(date(2026, 3, 1))


class TestHistorialAcademico:
    def test_construccion_valida(self) -> None:
        registro = HistorialAcademico(
            persona_master_id=1, clave_titulo="x", tipo_cambio=TipoCambioAcademico.TITULO_NUEVO,
            detectado_en=_AHORA, consulta_senescyt_id=1,
        )
        assert registro.ejecutado_por == "sistema"

    def test_sin_cambios_falla(self) -> None:
        with pytest.raises(HistorialAcademicoInvalidoError):
            HistorialAcademico(
                persona_master_id=1, clave_titulo="x", tipo_cambio=TipoCambioAcademico.SIN_CAMBIOS,
                detectado_en=_AHORA, consulta_senescyt_id=1,
            )

    def test_persona_master_id_none_falla(self) -> None:
        with pytest.raises(HistorialAcademicoInvalidoError):
            HistorialAcademico(
                persona_master_id=None, clave_titulo="x", tipo_cambio=TipoCambioAcademico.TITULO_NUEVO,  # type: ignore[arg-type]
                detectado_en=_AHORA, consulta_senescyt_id=1,
            )


class TestConsultaSenescyt:
    def test_construccion_valida(self) -> None:
        consulta = ConsultaSenescyt(persona_master_id=1, iniciado_en=_AHORA)
        assert consulta.exito is None

    def test_persona_master_id_none_falla(self) -> None:
        with pytest.raises(ConsultaSenescytInvalidaError):
            ConsultaSenescyt(persona_master_id=None, iniciado_en=_AHORA)  # type: ignore[arg-type]

    def test_reintentos_negativos_falla(self) -> None:
        with pytest.raises(ConsultaSenescytInvalidaError):
            ConsultaSenescyt(persona_master_id=1, iniciado_en=_AHORA, reintentos=-1)

    def test_finalizar_antes_de_iniciado_falla(self) -> None:
        consulta = ConsultaSenescyt(persona_master_id=1, iniciado_en=_AHORA)
        with pytest.raises(ConsultaSenescytInvalidaError):
            consulta.finalizar(exito=True, cuando=datetime(2025, 1, 1, tzinfo=UTC), duracion_segundos=1.0)

    def test_finalizar_marca_todos_los_campos(self) -> None:
        consulta = ConsultaSenescyt(persona_master_id=1, iniciado_en=_AHORA)
        despues = datetime(2026, 1, 1, 0, 0, 5, tzinfo=UTC)
        consulta.finalizar(
            exito=True, cuando=despues, duracion_segundos=5.0, version_resultante=2,
            respuesta_cruda={"titulos": []}, cache_utilizado=True,
        )
        assert consulta.exito is True
        assert consulta.version_resultante == 2
        assert consulta.cache_utilizado is True

    def test_registrar_reintento(self) -> None:
        consulta = ConsultaSenescyt(persona_master_id=1, iniciado_en=_AHORA)
        consulta.registrar_reintento()
        assert consulta.reintentos == 1


class TestEventoAcademico:
    def test_construccion_valida(self) -> None:
        evento = EventoAcademico(tipo=TipoEventoAcademico.TITULO_NUEVO, persona_master_id=1, payload={}, creado_en=_AHORA)
        assert evento.estado.value == "pendiente"

    def test_persona_master_id_none_falla(self) -> None:
        with pytest.raises(EventoAcademicoInvalidoError):
            EventoAcademico(
                tipo=TipoEventoAcademico.TITULO_NUEVO, persona_master_id=None, payload={}, creado_en=_AHORA  # type: ignore[arg-type]
            )

    def test_consumir_luego_procesar(self) -> None:
        evento = EventoAcademico(tipo=TipoEventoAcademico.TITULO_NUEVO, persona_master_id=1, payload={}, creado_en=_AHORA)
        evento.consumir(_AHORA)
        evento.procesar(_AHORA)
        assert evento.procesado_en == _AHORA

    def test_procesar_sin_consumir_falla(self) -> None:
        evento = EventoAcademico(tipo=TipoEventoAcademico.TITULO_NUEVO, persona_master_id=1, payload={}, creado_en=_AHORA)
        with pytest.raises(EventoAcademicoInvalidoError):
            evento.procesar(_AHORA)


class TestAlertaAcademica:
    def test_construccion_valida(self) -> None:
        alerta = AlertaAcademica(
            persona_master_id=1, tipo=TipoAlertaAcademica.NUEVO_TITULO, prioridad=NivelCriticidad.MEDIO,
            descripcion="x", detectado_en=_AHORA,
        )
        assert alerta.estado == EstadoAlertaAcademica.PENDIENTE

    def test_persona_master_id_none_falla(self) -> None:
        with pytest.raises(AlertaAcademicaInvalidaError):
            AlertaAcademica(
                persona_master_id=None, tipo=TipoAlertaAcademica.NUEVO_TITULO,  # type: ignore[arg-type]
                prioridad=NivelCriticidad.MEDIO, descripcion="x", detectado_en=_AHORA,
            )

    def test_descripcion_vacia_falla(self) -> None:
        with pytest.raises(AlertaAcademicaInvalidaError):
            AlertaAcademica(
                persona_master_id=1, tipo=TipoAlertaAcademica.NUEVO_TITULO, prioridad=NivelCriticidad.MEDIO,
                descripcion="  ", detectado_en=_AHORA,
            )

    def test_marcar_enviada_y_descartar(self) -> None:
        alerta = AlertaAcademica(
            persona_master_id=1, tipo=TipoAlertaAcademica.NUEVO_TITULO, prioridad=NivelCriticidad.MEDIO,
            descripcion="x", detectado_en=_AHORA,
        )
        alerta.marcar_enviada()
        assert alerta.estado.value == "enviada"
        alerta.descartar()
        assert alerta.estado.value == "descartada"


def test_estado_registro_academico_desconocido_es_valido() -> None:
    titulo = TituloAcademico(
        persona_master_id=1, clave_titulo="x", titulo="Abogado", nivel="Tercer Nivel", institucion="UCE",
        estado=EstadoRegistroAcademico.DESCONOCIDO,
    )
    assert titulo.estado == EstadoRegistroAcademico.DESCONOCIDO
