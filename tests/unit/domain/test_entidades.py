"""Tests: Entidades de dominio."""

from __future__ import annotations

from datetime import date

import pytest

from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.historial_cambios import (
    HistorialCambios,
    HistorialCambiosInvalidoError,
)
from govdata.domain.entities.persona import Persona
from govdata.domain.exceptions.domain_exceptions import (
    EntidadInvalidaError,
    FuncionarioInvalidoError,
)
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.cargo import Cargo
from govdata.domain.value_objects.correo import Correo
from govdata.domain.value_objects.nombre_completo import NombreCompleto


class TestEntidad:
    def test_crea_entidad_valida(self) -> None:
        entidad = Entidad(
            nombre="Defensoria del Pueblo",
            url_transparencia="https://transparencia.dpe.gob.ec/entidades/dpe",
            portal_origen="DPE",
        )
        assert entidad.portal_origen == "dpe"  # normalizado a minusculas
        assert entidad.activo is True

    def test_rechaza_nombre_vacio(self) -> None:
        with pytest.raises(EntidadInvalidaError):
            Entidad(nombre="", url_transparencia="https://x.com", portal_origen="dpe")


class TestPersona:
    def test_persona_valida_sin_contacto(self) -> None:
        persona = Persona(nombre_completo=NombreCompleto("Juan", "Perez"))
        assert persona.correo is None

    def test_actualizar_datos_contacto_no_borra_datos_previos(self) -> None:
        persona = Persona(
            nombre_completo=NombreCompleto("Juan", "Perez"),
            correo=Correo("juan@x.com"),
        )
        persona.actualizar_datos_contacto(telefono=None)
        assert persona.correo == Correo("juan@x.com")

    def test_actualizar_datos_contacto_enriquece(self) -> None:
        persona = Persona(nombre_completo=NombreCompleto("Juan", "Perez"))
        persona.actualizar_datos_contacto(correo=Correo("juan@x.com"))
        assert persona.correo == Correo("juan@x.com")


class TestFuncionario:
    def test_funcionario_valido_es_vigente_sin_fecha_fin(self) -> None:
        funcionario = Funcionario(
            persona_id=1,
            entidad_id=1,
            cargo=Cargo("Director Juridico"),
            dependencia="Procuraduria",
            area_clasificada=AreaRelevante.JURIDICA,
        )
        assert funcionario.vigente is True

    def test_finalizar_cierra_vigencia(self) -> None:
        funcionario = Funcionario(
            persona_id=1,
            entidad_id=1,
            cargo=Cargo("Director Juridico"),
            dependencia="Procuraduria",
            area_clasificada=AreaRelevante.JURIDICA,
            fecha_inicio=date(2026, 1, 1),
        )
        funcionario.finalizar(date(2027, 1, 1))
        assert funcionario.vigente is False

    def test_rechaza_fecha_fin_anterior_a_inicio(self) -> None:
        with pytest.raises(FuncionarioInvalidoError):
            Funcionario(
                persona_id=1,
                entidad_id=1,
                cargo=Cargo("Director Juridico"),
                dependencia="Procuraduria",
                area_clasificada=AreaRelevante.JURIDICA,
                fecha_inicio=date(2027, 1, 1),
                fecha_fin=date(2026, 1, 1),
            )

    def test_rechaza_score_fuera_de_rango(self) -> None:
        with pytest.raises(FuncionarioInvalidoError):
            Funcionario(
                persona_id=1,
                entidad_id=1,
                cargo=Cargo("Director Juridico"),
                dependencia="Procuraduria",
                area_clasificada=AreaRelevante.JURIDICA,
                score_clasificacion=150.0,
            )


class TestHistorialCambios:
    def test_registra_cambio_de_cargo(self) -> None:
        cambio = HistorialCambios(
            persona_id=1,
            entidad_id=1,
            campo_modificado="cargo",
            valor_anterior="Director Juridico",
            valor_nuevo="Procurador",
            detectado_en=date(2027, 1, 1),
        )
        assert cambio.valor_nuevo == "Procurador"

    def test_rechaza_cambio_sin_diferencia_real(self) -> None:
        with pytest.raises(HistorialCambiosInvalidoError):
            HistorialCambios(
                persona_id=1,
                entidad_id=1,
                campo_modificado="cargo",
                valor_anterior="Director Juridico",
                valor_nuevo="Director Juridico",
                detectado_en=date(2027, 1, 1),
            )
