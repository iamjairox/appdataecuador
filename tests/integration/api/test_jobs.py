"""Tests: GET /jobs/{job_id} -- Modulo 10."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from govdata.application.services.auditoria_orquestacion_service import AuditoriaOrquestacionService
from govdata.application.services.cola_trabajos_orquestador_service import (
    ColaTrabajosOrquestadorService,
)
from govdata.domain.value_objects.tipo_paso_pipeline import TipoPasoPipeline
from govdata.domain.value_objects.tipo_trabajo_orquestador import TipoTrabajoOrquestador
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_auditoria_etapa_repository import (
    SqlAlchemyAuditoriaEtapaRepository,
)
from govdata.infrastructure.persistence.postgresql.repositories.sqlalchemy_trabajo_orquestador_repository import (
    SqlAlchemyTrabajoOrquestadorRepository,
)

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestObtenerEstadoJob:
    def test_job_existente_incluye_etapas(self, cliente, sesion) -> None:
        cola = ColaTrabajosOrquestadorService(SqlAlchemyTrabajoOrquestadorRepository(sesion), ahora_provider=lambda: _AHORA)
        trabajo = cola.encolar(TipoTrabajoOrquestador.CONSULTA_ENTIDAD, {"nombre_entidad": "X"}, "consulta_rapida")
        cola.iniciar_directo(trabajo)
        cola.marcar_completado(trabajo)

        auditoria = AuditoriaOrquestacionService(SqlAlchemyAuditoriaEtapaRepository(sesion))
        auditoria.registrar_ejecutado(str(trabajo.id), TipoPasoPipeline.DESCUBRIMIENTO, _AHORA, _AHORA)
        sesion.flush()

        respuesta = cliente.get(f"/api/v1/jobs/{trabajo.id}")

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["id"] == str(trabajo.id)
        assert cuerpo["estado"] == "completado"
        assert len(cuerpo["etapas"]) == 1
        assert cuerpo["etapas"][0]["tipo_paso"] == "descubrimiento"

    def test_job_inexistente_da_404(self, cliente) -> None:
        respuesta = cliente.get(f"/api/v1/jobs/{uuid.uuid4()}")
        assert respuesta.status_code == 404

    def test_job_id_no_uuid_da_422(self, cliente) -> None:
        respuesta = cliente.get("/api/v1/jobs/no-es-un-uuid")
        assert respuesta.status_code == 422
