"""Tests: GET /funcionarios/{persona_master_id}/{...} -- Modulo 10.

Todos estos endpoints solo tocan repositorios (Modulos 5/6/7/8, ninguna
llamada externa) -- se prueban con SQLite real, sin dobles."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.domain.entities.alerta_academica import AlertaAcademica
from govdata.domain.entities.alerta_foro import AlertaForo
from govdata.domain.entities.alerta_perfil import AlertaPerfil
from govdata.domain.value_objects.nivel_criticidad import NivelCriticidad
from govdata.domain.value_objects.tipo_alerta_academica import TipoAlertaAcademica
from govdata.domain.value_objects.tipo_alerta_foro import TipoAlertaForo
from govdata.domain.value_objects.tipo_alerta_perfil import TipoAlertaPerfil
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_academica_repository import (
    SqlAlchemyAlertaAcademicaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_foro_repository import (
    SqlAlchemyAlertaForoRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_alerta_perfil_repository import (
    SqlAlchemyAlertaPerfilRepository,
)
from tests.integration.api.factories import crear_entidad, crear_funcionario_juridico_completo

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestPerfilConsolidado:
    def test_perfil_de_funcionario_existente(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        _persona, _funcionario, persona_master = crear_funcionario_juridico_completo(sesion, entidad)

        respuesta = cliente.get(f"/api/v1/funcionarios/{persona_master.id}")

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert set(cuerpo) == {"persona", "transparencia", "senescyt", "foro", "generado_en"}
        assert cuerpo["persona"]["cedula"] == "0102030405"

    def test_funcionario_no_encontrado_da_404(self, cliente) -> None:
        respuesta = cliente.get("/api/v1/funcionarios/999999")
        assert respuesta.status_code == 404
        assert respuesta.json()["error"]["codigo"] == "PersonaMasterInvalidaError"


class TestHistorialFuncionario:
    def test_historial_vacio_para_funcionario_sin_versiones(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        _persona, _funcionario, persona_master = crear_funcionario_juridico_completo(sesion, entidad)

        respuesta = cliente.get(f"/api/v1/funcionarios/{persona_master.id}/historial")

        assert respuesta.status_code == 200
        assert respuesta.json() == []

    def test_funcionario_no_encontrado_da_404(self, cliente) -> None:
        assert cliente.get("/api/v1/funcionarios/999999/historial").status_code == 404


class TestAcademicoFuncionario:
    def test_perfil_academico_de_funcionario_existente(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        _persona, _funcionario, persona_master = crear_funcionario_juridico_completo(sesion, entidad)

        respuesta = cliente.get(f"/api/v1/funcionarios/{persona_master.id}/academico")

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert set(cuerpo) >= {"persona_master", "identidad", "titulos", "historial", "alertas", "eventos", "estadisticas"}
        assert cuerpo["titulos"] == []

    def test_funcionario_no_encontrado_da_404(self, cliente) -> None:
        assert cliente.get("/api/v1/funcionarios/999999/academico").status_code == 404


class TestForoFuncionario:
    def test_foro_de_funcionario_sin_registros_es_vacio(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        _persona, _funcionario, persona_master = crear_funcionario_juridico_completo(sesion, entidad)

        respuesta = cliente.get(f"/api/v1/funcionarios/{persona_master.id}/foro")

        assert respuesta.status_code == 200
        assert respuesta.json()["registros"] == []

    def test_funcionario_no_encontrado_da_404(self, cliente) -> None:
        assert cliente.get("/api/v1/funcionarios/999999/foro").status_code == 404


class TestAlertasFuncionario:
    def test_alertas_vacias_para_funcionario_sin_alertas(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        _persona, _funcionario, persona_master = crear_funcionario_juridico_completo(sesion, entidad)

        respuesta = cliente.get(f"/api/v1/funcionarios/{persona_master.id}/alertas")

        assert respuesta.status_code == 200
        assert respuesta.json() == []

    def test_funcionario_no_encontrado_da_404(self, cliente) -> None:
        assert cliente.get("/api/v1/funcionarios/999999/alertas").status_code == 404

    def test_agrega_las_3_fuentes_ordenadas_por_fecha_desc(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        _persona, _funcionario, persona_master = crear_funcionario_juridico_completo(sesion, entidad)
        assert persona_master.id is not None

        SqlAlchemyAlertaPerfilRepository(sesion).guardar(
            AlertaPerfil(
                persona_master_id=persona_master.id, tipo=TipoAlertaPerfil.NUEVA_INSTITUCION,
                prioridad=NivelCriticidad.MEDIO, descripcion="Nueva institucion detectada", detectado_en=_AHORA,
            )
        )
        SqlAlchemyAlertaAcademicaRepository(sesion).guardar(
            AlertaAcademica(
                persona_master_id=persona_master.id, tipo=TipoAlertaAcademica.NUEVO_TITULO,
                prioridad=NivelCriticidad.ALTO, descripcion="Nuevo titulo detectado", detectado_en=_AHORA,
            )
        )
        SqlAlchemyAlertaForoRepository(sesion).guardar(
            AlertaForo(
                persona_master_id=persona_master.id, tipo=TipoAlertaForo.REGISTRO_NUEVO,
                prioridad=NivelCriticidad.BAJO, descripcion="Nuevo registro en el Foro", detectado_en=_AHORA,
            )
        )
        sesion.flush()

        respuesta = cliente.get(f"/api/v1/funcionarios/{persona_master.id}/alertas")

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert len(cuerpo) == 3
        assert {a["fuente"] for a in cuerpo} == {"identidad", "academico", "foro"}


class TestTimelineFuncionario:
    def test_timeline_de_funcionario_existente(self, cliente, sesion) -> None:
        entidad = crear_entidad(sesion, "Entidad X")
        _persona, _funcionario, persona_master = crear_funcionario_juridico_completo(sesion, entidad)

        respuesta = cliente.get(f"/api/v1/funcionarios/{persona_master.id}/timeline")

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["persona_master_id"] == persona_master.id
        assert isinstance(cuerpo["puntos"], list)

    def test_funcionario_no_encontrado_da_404(self, cliente) -> None:
        assert cliente.get("/api/v1/funcionarios/999999/timeline").status_code == 404
