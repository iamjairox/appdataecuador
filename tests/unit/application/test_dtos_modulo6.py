"""Tests: DTOs del Modulo 6 con conversion `.desde_entidad()` -- cierran
la cobertura de las conversiones de presentacion, ejercitadas de forma
indirecta en otros tests pero nunca de forma explicita y aislada."""

from __future__ import annotations

from datetime import UTC, datetime

from govdata.application.dto.atributo_trazable_dto import AtributoTrazableDTO
from govdata.application.dto.caso_revision_dto import CasoRevisionDTO
from govdata.application.dto.consulta_fuente_log_dto import ConsultaFuenteLogDTO
from govdata.domain.entities.atributo_trazable import AtributoTrazable
from govdata.domain.entities.caso_revision_identidad import CasoRevisionIdentidad
from govdata.domain.entities.consulta_fuente_log import ConsultaFuenteLog
from govdata.domain.value_objects.fuente_externa import FuenteExterna

_AHORA = datetime(2026, 1, 1, tzinfo=UTC)


class TestAtributoTrazableDTO:
    def test_desde_entidad(self) -> None:
        atributo = AtributoTrazable(
            persona_master_id=1, campo="titulo", valor="Abogado", fuente=FuenteExterna.SENESCYT,
            obtenido_en=_AHORA, score=90.0, registro_fuente_id=5,
        )
        dto = AtributoTrazableDTO.desde_entidad(atributo)
        assert dto.campo == "titulo"
        assert dto.valor == "Abogado"
        assert dto.fuente == "senescyt"
        assert dto.score == 90.0
        assert dto.registro_fuente_id == 5


class TestCasoRevisionDTO:
    def test_desde_entidad_caso_pendiente(self) -> None:
        caso = CasoRevisionIdentidad(
            persona_master_id_a=1, persona_master_id_b=2, score=90.0, explicacion="x",
            campos_utilizados=("correo", "fingerprint"), creado_en=_AHORA,
        )
        dto = CasoRevisionDTO.desde_entidad(caso)
        assert dto.id == str(caso.uuid)
        assert dto.estado == "pendiente_revision"
        assert dto.campos_utilizados == ("correo", "fingerprint")
        assert dto.resuelto_en is None

    def test_desde_entidad_caso_resuelto(self) -> None:
        caso = CasoRevisionIdentidad(
            persona_master_id_a=1, persona_master_id_b=2, score=95.0, explicacion="x",
            campos_utilizados=(), creado_en=_AHORA,
        )
        caso.aprobar("ana.revisora", _AHORA, criterio="manual")
        dto = CasoRevisionDTO.desde_entidad(caso)
        assert dto.estado == "aprobado"
        assert dto.resuelto_por == "ana.revisora"
        assert dto.criterio_resolucion == "manual"


class TestConsultaFuenteLogDTO:
    def test_desde_entidad_en_progreso(self) -> None:
        log = ConsultaFuenteLog(persona_master_id=1, fuente=FuenteExterna.SRI, iniciado_en=_AHORA)
        dto = ConsultaFuenteLogDTO.desde_entidad(log)
        assert dto.fuente == "sri"
        assert dto.exito is None
        assert dto.finalizado_en is None

    def test_desde_entidad_finalizado(self) -> None:
        log = ConsultaFuenteLog(persona_master_id=1, fuente=FuenteExterna.SRI, iniciado_en=_AHORA)
        log.finalizar(exito=True, cuando=_AHORA, duracion_segundos=2.5)
        dto = ConsultaFuenteLogDTO.desde_entidad(log)
        assert dto.exito is True
        assert dto.duracion_segundos == 2.5
