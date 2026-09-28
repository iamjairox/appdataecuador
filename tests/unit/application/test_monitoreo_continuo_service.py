"""Tests: MonitoreoContinuoService -- Submodulo 5.15 (flujo obligatorio
completo), con fakes para descubrimiento/descarga/extraccion/verificacion
remota."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from govdata.application.dto.resultado_descubrimiento_dto import ResultadoDescubrimientoEntidadDTO
from govdata.application.dto.resultado_unificado_dto import (
    DocumentoResumenDTO,
    EntidadResumenDTO,
    FuncionarioUnificadoDTO,
    ResultadoUnificadoDTO,
)
from govdata.application.services.alerta_service import AlertaService
from govdata.application.services.auditoria_comparacion_service import AuditoriaComparacionService
from govdata.application.services.evento_service import EventoService
from govdata.application.services.historial_service import HistorialService
from govdata.application.services.monitoreo_continuo_service import MonitoreoContinuoService
from govdata.application.services.oportunidad_comercial_service import OportunidadComercialService
from govdata.application.services.persistencia_inteligente_service import (
    PersistenciaInteligenteService,
)
from govdata.application.services.verificacion_service import VerificacionService
from govdata.application.use_cases.comparar_documentos_use_case import CompararDocumentosUseCase
from govdata.config.rule_engine import cargar_rule_engine
from govdata.domain.entities.documento import DocumentoTransparencia, EstadoDocumento, TipoArchivo
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.publicacion import PublicacionMensual
from govdata.domain.entities.verificacion import Verificacion
from govdata.domain.exceptions.domain_exceptions import GovDataError
from tests.unit.application.fakes import (
    FakeDocumentoRepository,
    FakeEntidadRepository,
    FakePublicacionRepository,
)
from tests.unit.application.fakes_extraccion import (
    FakeDescargaPort,
    FakeDescubrimientoPort,
    FakeExtraccionPort,
    FakeFuncionarioRepositoryExtraccion,
    FakePersonaRepository,
)
from tests.unit.application.fakes_modulo5 import (
    FakeAlertaRepository,
    FakeAuditoriaComparacionRepository,
    FakeEventoRepository,
    FakeOportunidadComercialRepository,
    FakeVerificacionRemota,
    FakeVerificacionRepository,
    FakeVersionFuncionarioRepository,
)

_RULE_ENGINE = cargar_rule_engine()


def _entidad(id_: int = 1, nombre: str = "Entidad X") -> Entidad:
    return Entidad(id=id_, nombre=nombre, url_transparencia=f"https://x/{id_}", portal_origen="dpe")


def _construir_servicio(
    descubrimiento, descarga, extraccion, verificacion_remota,
    publicacion_repo=None, documento_repo=None, funcionario_repo=None, persona_repo=None, entidad_repo=None,
):
    publicacion_repo = publicacion_repo or FakePublicacionRepository()
    documento_repo = documento_repo or FakeDocumentoRepository()
    funcionario_repo = funcionario_repo or FakeFuncionarioRepositoryExtraccion()
    persona_repo = persona_repo or FakePersonaRepository()
    entidad_repo = entidad_repo or FakeEntidadRepository()

    version_repo = FakeVersionFuncionarioRepository()
    alerta_repo = FakeAlertaRepository()
    evento_repo = FakeEventoRepository()
    auditoria_repo = FakeAuditoriaComparacionRepository()
    oportunidad_repo = FakeOportunidadComercialRepository()
    verificacion_repo = FakeVerificacionRepository()

    historial = HistorialService(version_repo)
    persistencia = PersistenciaInteligenteService(persona_repo, funcionario_repo, historial)
    alerta_service = AlertaService(alerta_repo, _RULE_ENGINE.criticidad)
    oportunidad_service = OportunidadComercialService(oportunidad_repo, _RULE_ENGINE.criticidad)
    evento_service = EventoService(evento_repo)
    auditoria_service = AuditoriaComparacionService(auditoria_repo)
    verificacion_service = VerificacionService(verificacion_repo)
    comparar = CompararDocumentosUseCase(persistencia, alerta_service, oportunidad_service, evento_service, auditoria_service, _RULE_ENGINE)

    servicio = MonitoreoContinuoService(
        entidad_repository=entidad_repo,
        publicacion_repository=publicacion_repo,
        documento_repository=documento_repo,
        funcionario_repository=funcionario_repo,
        persona_repository=persona_repo,
        descubrimiento=descubrimiento,
        descarga=descarga,
        extraccion=extraccion,
        verificacion_remota=verificacion_remota,
        verificacion_service=verificacion_service,
        comparar_documentos=comparar,
    )
    return servicio, verificacion_repo, publicacion_repo, documento_repo


def _publicacion(mes=date(2026, 7, 1)) -> PublicacionMensual:
    return PublicacionMensual(id=1, entidad_id=1, mes_publicado=mes, url_item="https://x/item")


def _doc_descubierto(id_=1) -> DocumentoTransparencia:
    return DocumentoTransparencia(
        id=id_, publicacion_id=id_, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf",
        url_documento="https://x/d.pdf", estado=EstadoDocumento.DESCUBIERTO,
    )


def _doc_descargado(id_=1, hash_="b") -> DocumentoTransparencia:
    return DocumentoTransparencia(
        id=id_, publicacion_id=id_, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf",
        url_documento="https://x/d.pdf", estado=EstadoDocumento.DESCARGADO,
        hash_sha256=hash_ * 64, tamano_bytes=10, ruta_almacenamiento="file:///b",
    )


def _resultado_extraccion() -> ResultadoUnificadoDTO:
    return ResultadoUnificadoDTO(
        entidad=EntidadResumenDTO(id=1, nombre="Entidad X", portal_origen="dpe"),
        documento=DocumentoResumenDTO(id=1, tipo_archivo="pdf", mes_publicado=date(2026, 7, 1), hash_sha256="b" * 64, version=1, url="x"),
        funcionarios=[
            FuncionarioUnificadoDTO(
                nombre="Juan", apellido="Perez", cargo="Director Juridico", dependencia="Legal",
                correo="j@x.com", telefono="0999", area="juridica", score=95.0, fingerprint="JUANPEREZ",
            )
        ],
    )


class TestSinDocumentoNuevo:
    def test_sin_publicacion_registra_verificacion_sin_cambio(self) -> None:
        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(entidad=_entidad(), publicacion=None, documento=None, exito=False, error="x")
        servicio, verificacion_repo, *_ = _construir_servicio(
            FakeDescubrimientoPort(resultado_descubrimiento), FakeDescargaPort(), FakeExtraccionPort(None), FakeVerificacionRemota()
        )
        resultado = servicio.monitorear(_entidad())
        assert resultado.hubo_cambio is False
        assert resultado.verificacion.motivo == "sin_publicacion_o_documento"
        assert len(verificacion_repo.guardadas) == 1


class TestDocumentoYaProcesado:
    def test_no_reprocesa_documento_ya_verificado(self) -> None:
        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(
            entidad=_entidad(), publicacion=_publicacion(), documento=_doc_descubierto(), exito=True
        )
        descubrimiento = FakeDescubrimientoPort(resultado_descubrimiento)
        servicio, verificacion_repo, *_ = _construir_servicio(
            descubrimiento, FakeDescargaPort(), FakeExtraccionPort(_resultado_extraccion()), FakeVerificacionRemota()
        )
        verificacion_repo.registrar(
            Verificacion(entidad_id=1, hubo_cambio=True, motivo="previo", verificado_en=datetime.now(UTC), documento_id=1)
        )
        resultado = servicio.monitorear(_entidad())
        assert resultado.hubo_cambio is False
        assert resultado.verificacion.motivo == "documento_ya_procesado"


class TestHashSinCambiosViaHead:
    def test_hash_remoto_sin_cambios_no_descarga(self) -> None:
        publicacion_repo = FakePublicacionRepository()
        publicacion_repo.guardar_o_actualizar(PublicacionMensual(entidad_id=1, mes_publicado=date(2026, 6, 1), url_item="x"))
        documento_repo = FakeDocumentoRepository()
        documento_repo.guardar_o_actualizar(
            DocumentoTransparencia(
                publicacion_id=1, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf", url_documento="https://x/d.pdf",
                estado=EstadoDocumento.DESCARGADO, hash_sha256="a" * 64, tamano_bytes=10, ruta_almacenamiento="file:///a",
                etag="etag-viejo",
            )
        )
        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(
            entidad=_entidad(), publicacion=_publicacion(date(2026, 7, 1)), documento=_doc_descubierto(id_=2), exito=True
        )
        descarga = FakeDescargaPort(documento_resultado=_doc_descargado())
        servicio, _verificacion_repo, *_ = _construir_servicio(
            FakeDescubrimientoPort(resultado_descubrimiento), descarga, FakeExtraccionPort(_resultado_extraccion()),
            FakeVerificacionRemota(hay_cambios=False),
            publicacion_repo=publicacion_repo, documento_repo=documento_repo,
        )
        resultado = servicio.monitorear(_entidad())
        assert resultado.hubo_cambio is False
        assert resultado.verificacion.motivo == "hash_remoto_sin_cambios"
        assert descarga.llamadas == 0


class TestHashIdenticoTrasDescarga:
    def test_hash_igual_tras_descargar_no_extrae(self) -> None:
        publicacion_repo = FakePublicacionRepository()
        publicacion_repo.guardar_o_actualizar(PublicacionMensual(entidad_id=1, mes_publicado=date(2026, 6, 1), url_item="x"))
        documento_repo = FakeDocumentoRepository()
        documento_repo.guardar_o_actualizar(
            DocumentoTransparencia(
                publicacion_id=1, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf", url_documento="https://x/d.pdf",
                estado=EstadoDocumento.DESCARGADO, hash_sha256="b" * 64, tamano_bytes=10, ruta_almacenamiento="file:///b",
            )
        )
        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(
            entidad=_entidad(), publicacion=_publicacion(date(2026, 7, 1)), documento=_doc_descubierto(id_=2), exito=True
        )
        extraccion = FakeExtraccionPort(_resultado_extraccion())
        servicio, _verificacion_repo, *_ = _construir_servicio(
            FakeDescubrimientoPort(resultado_descubrimiento), FakeDescargaPort(documento_resultado=_doc_descargado(hash_="b")),
            extraccion, FakeVerificacionRemota(hay_cambios=True),
            publicacion_repo=publicacion_repo, documento_repo=documento_repo,
        )
        resultado = servicio.monitorear(_entidad())
        assert resultado.hubo_cambio is False
        assert resultado.verificacion.motivo == "hash_identico_tras_descarga"
        assert extraccion.llamadas == 0


class TestFlujoCompletoConCambios:
    def test_primera_vez_descarga_extrae_y_compara(self) -> None:
        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(
            entidad=_entidad(), publicacion=_publicacion(), documento=_doc_descubierto(), exito=True
        )
        servicio, _verificacion_repo, *_ = _construir_servicio(
            FakeDescubrimientoPort(resultado_descubrimiento), FakeDescargaPort(documento_resultado=_doc_descargado()),
            FakeExtraccionPort(_resultado_extraccion()), FakeVerificacionRemota(hay_cambios=True),
        )
        resultado = servicio.monitorear(_entidad())
        assert resultado.hubo_cambio is True
        assert resultado.comparacion is not None
        assert len(resultado.comparacion.nuevos) == 1


class TestMonitorearMasiva:
    def test_reutiliza_monitorear_por_cada_entidad(self) -> None:
        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(
            entidad=_entidad(), publicacion=_publicacion(), documento=_doc_descubierto(), exito=True
        )
        descubrimiento = FakeDescubrimientoPort(resultado_descubrimiento)
        servicio, *_ = _construir_servicio(
            descubrimiento, FakeDescargaPort(documento_resultado=_doc_descargado()),
            FakeExtraccionPort(_resultado_extraccion()), FakeVerificacionRemota(hay_cambios=True),
        )
        entidades = [_entidad(1, "A"), _entidad(2, "B")]
        resultados = servicio.monitorear_masiva(entidades)
        assert len(resultados) == 2
        assert descubrimiento.llamadas == 2

    def test_un_fallo_no_detiene_el_lote(self) -> None:
        class _DescubrimientoQueFalla:
            def descubrir(self, entidad):
                raise GovDataError("fallo simulado")

        servicio, *_ = _construir_servicio(
            _DescubrimientoQueFalla(), FakeDescargaPort(), FakeExtraccionPort(_resultado_extraccion()), FakeVerificacionRemota()
        )
        resultados = servicio.monitorear_masiva([_entidad(1, "A"), _entidad(2, "B")])
        assert resultados == []


class TestErrores:
    def test_entidad_sin_id_lanza_error(self) -> None:
        servicio, *_ = _construir_servicio(
            FakeDescubrimientoPort(ResultadoDescubrimientoEntidadDTO(entidad=_entidad(), publicacion=None, documento=None, exito=False)),
            FakeDescargaPort(), FakeExtraccionPort(None), FakeVerificacionRemota(),
        )
        entidad_sin_id = Entidad(nombre="X", url_transparencia="https://x/1", portal_origen="dpe")
        with pytest.raises(GovDataError):
            servicio.monitorear(entidad_sin_id)
