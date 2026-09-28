"""Tests: CompararDocumentosUseCase -- orquestacion completa del
Submodulo 5.1 (Motor de Comparacion -> Persistencia -> Alertas ->
Oportunidades -> Eventos -> Auditoria) con fakes."""

from __future__ import annotations

from datetime import date

import pytest

from govdata.application.dto.resultado_unificado_dto import FuncionarioUnificadoDTO
from govdata.application.services.alerta_service import AlertaService
from govdata.application.services.auditoria_comparacion_service import AuditoriaComparacionService
from govdata.application.services.evento_service import EventoService
from govdata.application.services.historial_service import HistorialService
from govdata.application.services.oportunidad_comercial_service import OportunidadComercialService
from govdata.application.services.persistencia_inteligente_service import (
    PersistenciaInteligenteService,
)
from govdata.application.use_cases.comparar_documentos_use_case import CompararDocumentosUseCase
from govdata.config.rule_engine import cargar_rule_engine
from govdata.domain.entities.documento import DocumentoTransparencia, EstadoDocumento, TipoArchivo
from govdata.domain.entities.entidad import Entidad
from govdata.domain.exceptions.domain_exceptions import ComparacionFallidaError
from tests.unit.application.fakes_extraccion import (
    FakeFuncionarioRepositoryExtraccion,
    FakePersonaRepository,
)
from tests.unit.application.fakes_modulo5 import (
    FakeAlertaRepository,
    FakeAuditoriaComparacionRepository,
    FakeEventoRepository,
    FakeOportunidadComercialRepository,
    FakeVersionFuncionarioRepository,
)

_RULE_ENGINE = cargar_rule_engine()


def _entidad() -> Entidad:
    return Entidad(id=1, nombre="Entidad X", url_transparencia="https://x/1", portal_origen="dpe")


def _documento(id_: int, hash_: str, version: int = 1) -> DocumentoTransparencia:
    return DocumentoTransparencia(
        id=id_, publicacion_id=id_, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf",
        url_documento="https://x/d.pdf", estado=EstadoDocumento.DESCARGADO,
        hash_sha256=hash_ * 64, tamano_bytes=10, ruta_almacenamiento="file:///a", version=version,
    )


def _f(fp: str, cargo: str = "Director Juridico", nombre: str = "Juan", apellido: str = "Perez") -> FuncionarioUnificadoDTO:
    return FuncionarioUnificadoDTO(
        nombre=nombre, apellido=apellido, cargo=cargo, dependencia="Legal", correo=f"{fp}@x.com",
        telefono="0999", area="juridica", score=95.0, fingerprint=fp,
    )


def _caso_uso() -> tuple[CompararDocumentosUseCase, dict]:
    persona_repo = FakePersonaRepository()
    funcionario_repo = FakeFuncionarioRepositoryExtraccion()
    version_repo = FakeVersionFuncionarioRepository()
    alerta_repo = FakeAlertaRepository()
    evento_repo = FakeEventoRepository()
    auditoria_repo = FakeAuditoriaComparacionRepository()
    oportunidad_repo = FakeOportunidadComercialRepository()

    historial = HistorialService(version_repo)
    persistencia = PersistenciaInteligenteService(persona_repo, funcionario_repo, historial)
    alerta_service = AlertaService(alerta_repo, _RULE_ENGINE.criticidad)
    oportunidad_service = OportunidadComercialService(oportunidad_repo, _RULE_ENGINE.criticidad)
    evento_service = EventoService(evento_repo)
    auditoria_service = AuditoriaComparacionService(auditoria_repo)

    caso_uso = CompararDocumentosUseCase(
        persistencia, alerta_service, oportunidad_service, evento_service, auditoria_service, _RULE_ENGINE
    )
    repos = {
        "persona": persona_repo, "funcionario": funcionario_repo, "version": version_repo,
        "alerta": alerta_repo, "evento": evento_repo, "auditoria": auditoria_repo, "oportunidad": oportunidad_repo,
    }
    return caso_uso, repos


class TestFlujoCompleto:
    def test_produce_el_contrato_oficial_con_las_cuatro_listas(self) -> None:
        caso_uso, _repos = _caso_uso()
        anteriores = [_f("A", cargo="Asesor Juridico")]
        actuales = [_f("A", cargo="Director Juridico"), _f("B", nombre="Maria", apellido="Lopez", cargo="Procurador")]

        resultado = caso_uso.ejecutar(
            _entidad(), _documento(1, "a"), _documento(2, "b"), anteriores, actuales,
            mes_publicado_actual=date(2026, 7, 1), mes_publicado_anterior=date(2026, 6, 1),
        )

        assert len(resultado.nuevos) == 1
        assert len(resultado.cambios) == 1
        assert resultado.eliminados == []
        assert resultado.sin_cambios == []
        assert resultado.estadisticas is not None
        assert len(resultado.alertas) >= 1

    def test_persiste_historial_alertas_eventos_y_auditoria(self) -> None:
        caso_uso, repos = _caso_uso()
        actuales = [_f("A", cargo="Director Juridico")]

        caso_uso.ejecutar(_entidad(), None, _documento(1, "a"), [], actuales, mes_publicado_actual=date(2026, 6, 1))

        assert len(repos["persona"].guardadas) == 1
        assert len(repos["version"].guardadas) == 1
        assert len(repos["alerta"].guardadas) >= 1
        assert len(repos["evento"].guardados) >= 1
        assert len(repos["auditoria"].guardadas) == 1
        assert repos["auditoria"].guardadas[0].finalizado_en is not None
        assert repos["auditoria"].guardadas[0].cambios_detectados == 1

    def test_sin_documento_anterior_todo_es_nuevo(self) -> None:
        caso_uso, _repos = _caso_uso()
        actuales = [_f("A"), _f("B", nombre="Maria")]
        resultado = caso_uso.ejecutar(_entidad(), None, _documento(1, "a"), [], actuales, mes_publicado_actual=date(2026, 6, 1))
        assert len(resultado.nuevos) == 2
        assert resultado.documento_anterior is None


class TestErrores:
    def test_documento_actual_sin_id_lanza_comparacion_fallida(self) -> None:
        caso_uso, _ = _caso_uso()
        documento_sin_id = DocumentoTransparencia(
            publicacion_id=1, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf", url_documento="https://x/d.pdf"
        )
        with pytest.raises(ComparacionFallidaError):
            caso_uso.ejecutar(_entidad(), None, documento_sin_id, [], [], mes_publicado_actual=date(2026, 6, 1))
