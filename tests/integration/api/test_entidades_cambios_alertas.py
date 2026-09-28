"""Tests: GET /entidades/{id}/cambios, GET /entidades/{id}/alertas -- Modulo 10."""

from __future__ import annotations

from datetime import UTC, date, datetime

from govdata.application.dto.diferencia_dto import DiferenciaFuncionarioDTO
from govdata.config.container import Container
from govdata.domain.entities.alerta import Alerta, TipoAlerta
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_cambio import TipoCambio
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_repository import (
    SqlAlchemyAlertaRepository,
)
from tests.integration.api.factories import crear_entidad, crear_funcionario_juridico_completo

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestCambiosEntidad:
    def test_lista_versiones_del_historial_laboral(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        persona, funcionario, _pm = crear_funcionario_juridico_completo(sesion, entidad)

        historial_service = Container.crear_historial_service(sesion)
        diferencia = DiferenciaFuncionarioDTO(
            tipo_cambio=TipoCambio.FUNCIONARIO_NUEVO, fingerprint="x", nombre="Ana", apellido="Torres",
            cargo="Procurador", dependencia="Direccion Juridica", correo=None, telefono=None, area="juridica",
        )
        historial_service.aplicar_diferencia(
            diferencia, entidad.id, persona.id, funcionario.id, documento_id=1, fecha=date(2026, 1, 1),
        )
        sesion.flush()

        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}/cambios")

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["total"] == 1
        assert cuerpo["items"][0]["persona_id"] == persona.id
        assert cuerpo["items"][0]["tipo_cambio"] is None  # ver docstring: no persistido junto a la version

    def test_filtro_por_fecha(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        respuesta = cliente.get(
            f"/api/v1/entidades/{entidad.id}/cambios", params={"desde": "2020-01-01", "hasta": "2020-12-31"},
        )
        assert respuesta.status_code == 200
        assert respuesta.json()["total"] == 0

    def test_entidad_no_encontrada_da_404(self, cliente) -> None:
        assert cliente.get("/api/v1/entidades/999999/cambios").status_code == 404


class TestAlertasEntidad:
    def test_lista_alertas_persistidas_ordenadas_por_fecha_desc(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        assert entidad.id is not None
        repo = SqlAlchemyAlertaRepository(sesion)
        repo.guardar(
            Alerta(
                entidad_id=entidad.id, tipo=TipoAlerta.NUEVO_PROCURADOR, prioridad=NivelCriticidad.ALTO,
                descripcion="Nuevo procurador detectado", detectado_en=_AHORA,
            )
        )
        sesion.flush()

        respuesta = cliente.get(f"/api/v1/entidades/{entidad.id}/alertas")

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["total"] == 1
        assert cuerpo["items"][0]["tipo"] == "nuevo_procurador"
        assert cuerpo["items"][0]["prioridad"] == "alto"

    def test_entidad_no_encontrada_da_404(self, cliente) -> None:
        assert cliente.get("/api/v1/entidades/999999/alertas").status_code == 404
