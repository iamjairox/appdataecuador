"""Tests: `.to_dict()` de los DTOs planos del Modulo 10 -- cada uno es un
metodo de conveniencia (logging/depuracion), no usado por los schemas
Pydantic (que leen atributos via `from_attributes=True`), pero forma
parte del contrato publico del DTO igual que en el resto del sistema."""

from __future__ import annotations

from datetime import UTC, date, datetime

from govdata.application.dto.alerta_funcionario_dto import AlertaFuncionarioDTO
from govdata.application.dto.cambio_entidad_dto import CambioEntidadDTO
from govdata.application.dto.entidad_listado_dto import EntidadListadoDTO
from govdata.application.dto.job_estado_dto import JobEstadoDTO
from govdata.application.dto.trabajo_orquestador_dto import TrabajoOrquestadorDTO

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


def test_alerta_funcionario_dto_to_dict() -> None:
    dto = AlertaFuncionarioDTO(
        id="1", fuente="identidad", tipo="nueva_institucion", prioridad="medio",
        descripcion="x", detectado_en=_AHORA, estado="pendiente",
    )
    assert dto.to_dict()["fuente"] == "identidad"


def test_cambio_entidad_dto_to_dict() -> None:
    dto = CambioEntidadDTO(
        persona_id=1, numero_version=1, cargo="Procurador", dependencia="Direccion Juridica",
        fecha_inicio=date(2026, 1, 1), fecha_fin=None, tipo_cambio=None, criticidad=None,
    )
    assert dto.to_dict()["persona_id"] == 1


def test_entidad_listado_dto_to_dict() -> None:
    dto = EntidadListadoDTO(
        id=1, nombre="Entidad X", tipo=None, provincia=None, ciudad=None, portal_origen="dpe",
        estado="activa", ultima_publicacion=None, ultima_actualizacion=None,
    )
    assert dto.to_dict()["nombre"] == "Entidad X"


def test_job_estado_dto_to_dict() -> None:
    trabajo_dto = TrabajoOrquestadorDTO(
        id="job-1", tipo="consulta_entidad", estado="completado", prioridad="media", politica="consulta_rapida",
        parametros={}, version_lock=1, intentos=0, max_intentos=3, entidad_id=None, creado_en=_AHORA,
        actualizado_en=_AHORA, iniciado_en=_AHORA, finalizado_en=_AHORA, ultimo_error=None,
    )
    dto = JobEstadoDTO(trabajo=trabajo_dto, etapas=[])
    assert dto.to_dict()["trabajo"]["id"] == "job-1"
