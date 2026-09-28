"""Tests: invariantes de las 7 nuevas entidades de dominio del Modulo 6."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from govdata.domain.entities.alerta_perfil import AlertaPerfil
from govdata.domain.entities.atributo_trazable import AtributoTrazable
from govdata.domain.entities.caso_revision_identidad import CasoRevisionIdentidad
from govdata.domain.entities.consulta_fuente_log import ConsultaFuenteLog
from govdata.domain.entities.evento_perfil import EventoPerfil
from govdata.domain.entities.persona_master import PersonaMaster
from govdata.domain.entities.registro_fuente import RegistroFuente
from govdata.domain.exceptions.domain_exceptions import (
    AlertaPerfilInvalidaError,
    AtributoTrazableInvalidoError,
    CasoRevisionIdentidadInvalidoError,
    ConsultaFuenteLogInvalidoError,
    EventoPerfilInvalidoError,
    PersonaMasterInvalidaError,
    RegistroFuenteInvalidoError,
)
from govdata.domain.value_objects.estado_alerta_perfil import EstadoAlertaPerfil
from govdata.domain.value_objects.estado_persona_master import EstadoPersonaMaster
from govdata.domain.value_objects.estado_revision_identidad import EstadoRevisionIdentidad
from govdata.domain.value_objects.fuente_externa import FuenteExterna
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from govdata.domain.value_objects.tipo_alerta_perfil import TipoAlertaPerfil
from govdata.domain.value_objects.tipo_evento_identidad import TipoEventoIdentidad

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestPersonaMaster:
    def test_construccion_valida(self) -> None:
        pm = PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"))
        assert pm.activa
        assert pm.estado == EstadoPersonaMaster.ACTIVA

    def test_nivel_confianza_fuera_de_rango_falla(self) -> None:
        with pytest.raises(PersonaMasterInvalidaError):
            PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"), nivel_confianza=150.0)

    def test_cantidad_fuentes_negativa_falla(self) -> None:
        with pytest.raises(PersonaMasterInvalidaError):
            PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"), cantidad_fuentes=-1)

    def test_fusionada_sin_fusionada_en_id_falla(self) -> None:
        with pytest.raises(PersonaMasterInvalidaError):
            PersonaMaster(
                persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"), estado=EstadoPersonaMaster.FUSIONADA
            )

    def test_no_fusionada_con_fusionada_en_id_falla(self) -> None:
        with pytest.raises(PersonaMasterInvalidaError):
            PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"), fusionada_en_id=2)

    def test_fusionar_en_marca_estado_y_destino(self) -> None:
        pm = PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"), id=5)
        pm.fusionar_en(9)
        assert pm.estado == EstadoPersonaMaster.FUSIONADA
        assert pm.fusionada_en_id == 9
        assert not pm.activa

    def test_fusionar_en_si_misma_falla(self) -> None:
        pm = PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"), id=5)
        with pytest.raises(PersonaMasterInvalidaError):
            pm.fusionar_en(5)

    def test_registrar_nueva_fuente_incrementa_contador(self) -> None:
        pm = PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"))
        pm.registrar_nueva_fuente()
        assert pm.cantidad_fuentes == 2

    def test_enriquecer_contacto_nunca_sobreescribe_con_none(self) -> None:
        from govdata.domain.value_objects.correo import Correo

        pm = PersonaMaster(
            persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"), correo_principal=Correo("a@x.com")
        )
        pm.enriquecer_contacto(correo=None)
        assert str(pm.correo_principal) == "a@x.com"

    def test_enriquecer_contacto_asigna_correo_y_telefono_nuevos(self) -> None:
        from govdata.domain.value_objects.correo import Correo
        from govdata.domain.value_objects.telefono import Telefono

        pm = PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"))
        pm.enriquecer_contacto(correo=Correo("nuevo@x.com"), telefono=Telefono("0991111111"))
        assert str(pm.correo_principal) == "nuevo@x.com"
        assert str(pm.telefono_principal) == "0991111111"

    def test_persona_id_none_falla(self) -> None:
        with pytest.raises(PersonaMasterInvalidaError):
            PersonaMaster(persona_id=None, nombre_completo=NombreCompleto("Juan", "Perez"))  # type: ignore[arg-type]

    def test_cantidad_cargos_historicos_negativa_falla(self) -> None:
        with pytest.raises(PersonaMasterInvalidaError):
            PersonaMaster(
                persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"), cantidad_cargos_historicos=-1
            )

    def test_actualizar_cargos_historicos(self) -> None:
        pm = PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"))
        pm.actualizar_cargos_historicos(3)
        assert pm.cantidad_cargos_historicos == 3
        with pytest.raises(PersonaMasterInvalidaError):
            pm.actualizar_cargos_historicos(-1)

    def test_marcar_en_revision_y_activa_sobre_fusionada_falla(self) -> None:
        pm = PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"), id=5)
        pm.fusionar_en(9)
        with pytest.raises(PersonaMasterInvalidaError):
            pm.marcar_en_revision()
        with pytest.raises(PersonaMasterInvalidaError):
            pm.marcar_activa()

    def test_marcar_en_revision_y_activa_ciclo_normal(self) -> None:
        pm = PersonaMaster(persona_id=1, nombre_completo=NombreCompleto("Juan", "Perez"))
        pm.marcar_en_revision()
        assert pm.estado == EstadoPersonaMaster.EN_REVISION
        pm.marcar_activa()
        assert pm.estado == EstadoPersonaMaster.ACTIVA


class TestRegistroFuente:
    def test_construccion_valida(self) -> None:
        registro = RegistroFuente(
            persona_master_id=1, fuente=FuenteExterna.SENESCYT, version=1, datos={"titulo": "Abogado"}
        )
        assert registro.vigente

    def test_version_menor_a_uno_falla(self) -> None:
        with pytest.raises(RegistroFuenteInvalidoError):
            RegistroFuente(persona_master_id=1, fuente=FuenteExterna.SENESCYT, version=0, datos={"a": "b"})

    def test_datos_vacios_falla(self) -> None:
        with pytest.raises(RegistroFuenteInvalidoError):
            RegistroFuente(persona_master_id=1, fuente=FuenteExterna.SENESCYT, version=1, datos={})

    def test_persona_master_id_none_falla(self) -> None:
        with pytest.raises(RegistroFuenteInvalidoError):
            RegistroFuente(
                persona_master_id=None, fuente=FuenteExterna.SENESCYT, version=1, datos={"a": "b"}  # type: ignore[arg-type]
            )

    def test_cerrar_marca_no_vigente(self) -> None:
        registro = RegistroFuente(
            persona_master_id=1, fuente=FuenteExterna.SENESCYT, version=1, datos={"a": "b"}
        )
        registro.cerrar()
        assert not registro.vigente


class TestAtributoTrazable:
    def test_construccion_valida(self) -> None:
        atributo = AtributoTrazable(
            persona_master_id=1, campo="titulo", valor="Abogado", fuente=FuenteExterna.SENESCYT,
            obtenido_en=_AHORA, score=90.0,
        )
        assert atributo.campo == "titulo"

    def test_campo_vacio_falla(self) -> None:
        with pytest.raises(AtributoTrazableInvalidoError):
            AtributoTrazable(
                persona_master_id=1, campo="  ", valor="x", fuente=FuenteExterna.SENESCYT,
                obtenido_en=_AHORA, score=90.0,
            )

    def test_score_fuera_de_rango_falla(self) -> None:
        with pytest.raises(AtributoTrazableInvalidoError):
            AtributoTrazable(
                persona_master_id=1, campo="titulo", valor="x", fuente=FuenteExterna.SENESCYT,
                obtenido_en=_AHORA, score=150.0,
            )

    def test_persona_master_id_none_falla(self) -> None:
        with pytest.raises(AtributoTrazableInvalidoError):
            AtributoTrazable(
                persona_master_id=None, campo="titulo", valor="x", fuente=FuenteExterna.SENESCYT,  # type: ignore[arg-type]
                obtenido_en=_AHORA, score=90.0,
            )


class TestCasoRevisionIdentidad:
    def test_construccion_valida(self) -> None:
        caso = CasoRevisionIdentidad(
            persona_master_id_a=1, persona_master_id_b=2, score=90.0, explicacion="x",
            campos_utilizados=("correo",), creado_en=_AHORA,
        )
        assert caso.estado == EstadoRevisionIdentidad.PENDIENTE_REVISION

    def test_sin_persona_b_ni_registro_fuente_falla(self) -> None:
        with pytest.raises(CasoRevisionIdentidadInvalidoError):
            CasoRevisionIdentidad(
                persona_master_id_a=1, score=90.0, explicacion="x", campos_utilizados=(), creado_en=_AHORA
            )

    def test_score_fuera_de_rango_falla(self) -> None:
        with pytest.raises(CasoRevisionIdentidadInvalidoError):
            CasoRevisionIdentidad(
                persona_master_id_a=1, persona_master_id_b=2, score=200.0, explicacion="x",
                campos_utilizados=(), creado_en=_AHORA,
            )

    def test_aprobar_transiciona_y_registra_auditoria(self) -> None:
        caso = CasoRevisionIdentidad(
            persona_master_id_a=1, persona_master_id_b=2, score=90.0, explicacion="x",
            campos_utilizados=(), creado_en=_AHORA,
        )
        caso.aprobar("ana.revisora", _AHORA, criterio="coincide correo institucional")
        assert caso.estado == EstadoRevisionIdentidad.APROBADO
        assert caso.resuelto_por == "ana.revisora"
        assert caso.criterio_resolucion == "coincide correo institucional"

    def test_rechazar_transiciona(self) -> None:
        caso = CasoRevisionIdentidad(
            persona_master_id_a=1, persona_master_id_b=2, score=90.0, explicacion="x",
            campos_utilizados=(), creado_en=_AHORA,
        )
        caso.rechazar("ana.revisora", _AHORA)
        assert caso.estado == EstadoRevisionIdentidad.RECHAZADO

    def test_no_se_puede_resolver_dos_veces(self) -> None:
        caso = CasoRevisionIdentidad(
            persona_master_id_a=1, persona_master_id_b=2, score=90.0, explicacion="x",
            campos_utilizados=(), creado_en=_AHORA,
        )
        caso.aprobar("ana", _AHORA)
        with pytest.raises(CasoRevisionIdentidadInvalidoError):
            caso.rechazar("pedro", _AHORA)

    def test_persona_master_id_a_none_falla(self) -> None:
        with pytest.raises(CasoRevisionIdentidadInvalidoError):
            CasoRevisionIdentidad(
                persona_master_id_a=None, persona_master_id_b=2, score=90.0, explicacion="x",  # type: ignore[arg-type]
                campos_utilizados=(), creado_en=_AHORA,
            )

    def test_estado_resuelto_sin_resuelto_en_ni_resuelto_por_falla(self) -> None:
        with pytest.raises(CasoRevisionIdentidadInvalidoError):
            CasoRevisionIdentidad(
                persona_master_id_a=1, persona_master_id_b=2, score=90.0, explicacion="x",
                campos_utilizados=(), creado_en=_AHORA, estado=EstadoRevisionIdentidad.APROBADO,
            )

    def test_estado_pendiente_con_resuelto_en_seteado_falla(self) -> None:
        with pytest.raises(CasoRevisionIdentidadInvalidoError):
            CasoRevisionIdentidad(
                persona_master_id_a=1, persona_master_id_b=2, score=90.0, explicacion="x",
                campos_utilizados=(), creado_en=_AHORA, resuelto_en=_AHORA,
            )


class TestConsultaFuenteLog:
    def test_construccion_valida(self) -> None:
        log = ConsultaFuenteLog(persona_master_id=1, fuente=FuenteExterna.SRI, iniciado_en=_AHORA)
        assert log.exito is None

    def test_reintentos_negativos_falla(self) -> None:
        with pytest.raises(ConsultaFuenteLogInvalidoError):
            ConsultaFuenteLog(persona_master_id=1, fuente=FuenteExterna.SRI, iniciado_en=_AHORA, reintentos=-1)

    def test_finalizar_antes_de_iniciado_falla(self) -> None:
        log = ConsultaFuenteLog(persona_master_id=1, fuente=FuenteExterna.SRI, iniciado_en=_AHORA)
        antes = datetime(2025, 1, 1, tzinfo=UTC)
        with pytest.raises(ConsultaFuenteLogInvalidoError):
            log.finalizar(exito=True, cuando=antes, duracion_segundos=1.0)

    def test_finalizar_marca_exito_y_duracion(self) -> None:
        log = ConsultaFuenteLog(persona_master_id=1, fuente=FuenteExterna.SRI, iniciado_en=_AHORA)
        despues = datetime(2026, 1, 1, 0, 0, 5, tzinfo=UTC)
        log.finalizar(exito=True, cuando=despues, duracion_segundos=5.0)
        assert log.exito is True
        assert log.duracion_segundos == 5.0

    def test_persona_master_id_none_falla(self) -> None:
        with pytest.raises(ConsultaFuenteLogInvalidoError):
            ConsultaFuenteLog(persona_master_id=None, fuente=FuenteExterna.SRI, iniciado_en=_AHORA)  # type: ignore[arg-type]

    def test_construir_con_finalizado_en_anterior_a_iniciado_en_falla(self) -> None:
        with pytest.raises(ConsultaFuenteLogInvalidoError):
            ConsultaFuenteLog(
                persona_master_id=1, fuente=FuenteExterna.SRI, iniciado_en=_AHORA,
                finalizado_en=datetime(2025, 1, 1, tzinfo=UTC),
            )


class TestEventoPerfil:
    def test_construccion_valida(self) -> None:
        evento = EventoPerfil(
            tipo=TipoEventoIdentidad.PERSONA_ENRIQUECIDA, persona_master_id=1, payload={}, creado_en=_AHORA
        )
        assert evento.estado.value == "pendiente"

    def test_consumir_luego_procesar(self) -> None:
        evento = EventoPerfil(
            tipo=TipoEventoIdentidad.PERSONA_ENRIQUECIDA, persona_master_id=1, payload={}, creado_en=_AHORA
        )
        evento.consumir(_AHORA)
        evento.procesar(_AHORA)
        assert evento.procesado_en == _AHORA

    def test_no_se_puede_procesar_sin_consumir(self) -> None:
        evento = EventoPerfil(
            tipo=TipoEventoIdentidad.PERSONA_ENRIQUECIDA, persona_master_id=1, payload={}, creado_en=_AHORA
        )
        with pytest.raises(EventoPerfilInvalidoError):
            evento.procesar(_AHORA)

    def test_persona_master_id_none_falla(self) -> None:
        with pytest.raises(EventoPerfilInvalidoError):
            EventoPerfil(
                tipo=TipoEventoIdentidad.PERSONA_ENRIQUECIDA, persona_master_id=None, payload={}, creado_en=_AHORA  # type: ignore[arg-type]
            )


class TestAlertaPerfil:
    def test_construccion_valida(self) -> None:
        alerta = AlertaPerfil(
            persona_master_id=1, tipo=TipoAlertaPerfil.TITULO_CAMBIADO, prioridad=NivelCriticidad.MEDIO,
            descripcion="cambio de titulo", detectado_en=_AHORA,
        )
        assert alerta.estado == EstadoAlertaPerfil.PENDIENTE

    def test_descripcion_vacia_falla(self) -> None:
        with pytest.raises(AlertaPerfilInvalidaError):
            AlertaPerfil(
                persona_master_id=1, tipo=TipoAlertaPerfil.TITULO_CAMBIADO, prioridad=NivelCriticidad.MEDIO,
                descripcion="   ", detectado_en=_AHORA,
            )

    def test_persona_master_id_none_falla(self) -> None:
        with pytest.raises(AlertaPerfilInvalidaError):
            AlertaPerfil(
                persona_master_id=None, tipo=TipoAlertaPerfil.TITULO_CAMBIADO,  # type: ignore[arg-type]
                prioridad=NivelCriticidad.MEDIO, descripcion="x", detectado_en=_AHORA,
            )

    def test_marcar_enviada_y_descartar(self) -> None:
        alerta = AlertaPerfil(
            persona_master_id=1, tipo=TipoAlertaPerfil.TITULO_CAMBIADO, prioridad=NivelCriticidad.MEDIO,
            descripcion="x", detectado_en=_AHORA,
        )
        alerta.marcar_enviada()
        assert alerta.estado == EstadoAlertaPerfil.ENVIADA
        alerta.descartar()
        assert alerta.estado == EstadoAlertaPerfil.DESCARTADA
