"""Tests: CacheService (Submodulo 4.9)."""

from __future__ import annotations

from datetime import UTC, date, datetime

from govdata.application.services.cache_service import CacheService
from govdata.domain.entities.documento import DocumentoTransparencia, EstadoDocumento, TipoArchivo
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.publicacion import PublicacionMensual
from govdata.domain.rules.reglas_configurables import ReglasCache
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.cargo import Cargo
from tests.unit.application.fakes import FakeDocumentoRepository, FakePublicacionRepository
from tests.unit.application.fakes_extraccion import FakeFuncionarioRepositoryExtraccion


def _documento_descargado(id_: int, descargado_en: datetime) -> DocumentoTransparencia:
    return DocumentoTransparencia(
        id=id_,
        publicacion_id=1,
        tipo_archivo=TipoArchivo.PDF,
        nombre_original="d.pdf",
        url_documento="https://x/d.pdf",
        estado=EstadoDocumento.DESCARGADO,
        hash_sha256="a" * 64,
        tamano_bytes=100,
        ruta_almacenamiento="file:///d.pdf",
        descargado_en=descargado_en,
    )


def _servicio(publicacion_repo, documento_repo, funcionario_repo, dias_vigencia=1, ahora=None):
    return CacheService(
        publicacion_repository=publicacion_repo,
        documento_repository=documento_repo,
        funcionario_repository=funcionario_repo,
        reglas=ReglasCache(dias_vigencia=dias_vigencia),
        ahora_provider=(lambda: ahora) if ahora else (lambda: datetime.now(UTC)),
    )


class TestEvaluarEntidad:
    def test_sin_publicacion_previa(self) -> None:
        servicio = _servicio(FakePublicacionRepository(), FakeDocumentoRepository(), FakeFuncionarioRepositoryExtraccion())
        decision = servicio.evaluar_entidad(1, date(2026, 6, 1))
        assert decision.vigente is False
        assert decision.motivo == "sin_publicacion_previa"

    def test_sin_documento_previo(self) -> None:
        pub_repo = FakePublicacionRepository()
        pub_repo.guardar_o_actualizar(PublicacionMensual(entidad_id=1, mes_publicado=date(2026, 6, 1), url_item="x"))
        servicio = _servicio(pub_repo, FakeDocumentoRepository(), FakeFuncionarioRepositoryExtraccion())
        decision = servicio.evaluar_entidad(1, date(2026, 6, 1))
        assert decision.vigente is False
        assert decision.motivo == "sin_documento_previo"

    def test_documento_no_descargado_no_es_vigente(self) -> None:
        pub_repo = FakePublicacionRepository()
        publicacion = pub_repo.guardar_o_actualizar(
            PublicacionMensual(entidad_id=1, mes_publicado=date(2026, 6, 1), url_item="x")
        )
        doc_repo = FakeDocumentoRepository()
        doc_repo.guardar_o_actualizar(
            DocumentoTransparencia(
                publicacion_id=publicacion.id, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf", url_documento="x"
            )
        )
        servicio = _servicio(pub_repo, doc_repo, FakeFuncionarioRepositoryExtraccion())
        decision = servicio.evaluar_entidad(1, date(2026, 6, 1))
        assert decision.vigente is False
        assert "documento_en_estado" in decision.motivo

    def test_documento_descargado_sin_fecha_no_es_vigente(self) -> None:
        """Caso borde: `Documento.estado == DESCARGADO` pero `descargado_en`
        quedo en `None` (dato inconsistente / migracion antigua) -- no debe
        crashear con un `TypeError` al restar fechas, sino degradar a
        "no vigente" de forma explicita."""
        pub_repo = FakePublicacionRepository()
        publicacion = pub_repo.guardar_o_actualizar(
            PublicacionMensual(entidad_id=1, mes_publicado=date(2026, 6, 1), url_item="x")
        )
        doc_repo = FakeDocumentoRepository()
        doc_repo.guardar_o_actualizar(
            DocumentoTransparencia(
                publicacion_id=publicacion.id,
                tipo_archivo=TipoArchivo.PDF,
                nombre_original="d.pdf",
                url_documento="x",
                estado=EstadoDocumento.DESCARGADO,
                hash_sha256="a" * 64,
                tamano_bytes=100,
                ruta_almacenamiento="file:///d.pdf",
                descargado_en=None,
            )
        )
        servicio = _servicio(pub_repo, doc_repo, FakeFuncionarioRepositoryExtraccion())
        decision = servicio.evaluar_entidad(1, date(2026, 6, 1))
        assert decision.vigente is False
        assert decision.motivo == "sin_fecha_descarga"

    def test_vigente_con_extraccion_reciente(self) -> None:
        pub_repo = FakePublicacionRepository()
        publicacion = pub_repo.guardar_o_actualizar(
            PublicacionMensual(entidad_id=1, mes_publicado=date(2026, 6, 1), url_item="x")
        )
        ahora = datetime(2026, 6, 10, tzinfo=UTC)
        doc_repo = FakeDocumentoRepository()
        documento = doc_repo.guardar_o_actualizar(
            _documento_descargado(1, descargado_en=datetime(2026, 6, 10, tzinfo=UTC))
        )
        documento.publicacion_id = publicacion.id

        func_repo = FakeFuncionarioRepositoryExtraccion()
        func_repo.guardar(
            Funcionario(
                persona_id=1,
                entidad_id=1,
                cargo=Cargo("Director Juridico"),
                dependencia="X",
                area_clasificada=AreaRelevante.JURIDICA,
                documento_id=documento.id,
            )
        )

        servicio = _servicio(pub_repo, doc_repo, func_repo, dias_vigencia=1, ahora=ahora)
        decision = servicio.evaluar_entidad(1, date(2026, 6, 1))
        assert decision.vigente is True
        assert decision.documento is not None

    def test_vigencia_expirada(self) -> None:
        pub_repo = FakePublicacionRepository()
        publicacion = pub_repo.guardar_o_actualizar(
            PublicacionMensual(entidad_id=1, mes_publicado=date(2026, 6, 1), url_item="x")
        )
        doc_repo = FakeDocumentoRepository()
        documento = doc_repo.guardar_o_actualizar(
            _documento_descargado(1, descargado_en=datetime(2026, 6, 1, tzinfo=UTC))
        )
        documento.publicacion_id = publicacion.id

        func_repo = FakeFuncionarioRepositoryExtraccion()
        func_repo.guardar(
            Funcionario(
                persona_id=1, entidad_id=1, cargo=Cargo("Director Juridico"), dependencia="X",
                area_clasificada=AreaRelevante.JURIDICA, documento_id=documento.id,
            )
        )

        ahora = datetime(2026, 6, 10, tzinfo=UTC)  # 9 dias despues
        servicio = _servicio(pub_repo, doc_repo, func_repo, dias_vigencia=1, ahora=ahora)
        decision = servicio.evaluar_entidad(1, date(2026, 6, 1))
        assert decision.vigente is False
        assert decision.motivo == "vigencia_expirada"

    def test_sin_extraccion_previa_no_es_vigente(self) -> None:
        pub_repo = FakePublicacionRepository()
        pub_repo.guardar_o_actualizar(
            PublicacionMensual(entidad_id=1, mes_publicado=date(2026, 6, 1), url_item="x")
        )
        doc_repo = FakeDocumentoRepository()
        doc_repo.guardar_o_actualizar(_documento_descargado(1, descargado_en=datetime.now(UTC)))
        servicio = _servicio(pub_repo, doc_repo, FakeFuncionarioRepositoryExtraccion())
        decision = servicio.evaluar_entidad(1, date(2026, 6, 1))
        assert decision.vigente is False
        assert decision.motivo == "sin_extraccion_previa"


class TestRequiereReextraccion:
    def test_true_si_no_hay_funcionarios(self) -> None:
        servicio = _servicio(FakePublicacionRepository(), FakeDocumentoRepository(), FakeFuncionarioRepositoryExtraccion())
        assert servicio.requiere_reextraccion(999) is True

    def test_false_si_ya_hay_funcionarios(self) -> None:
        func_repo = FakeFuncionarioRepositoryExtraccion()
        func_repo.guardar(
            Funcionario(
                persona_id=1, entidad_id=1, cargo=Cargo("Director Juridico"), dependencia="X",
                area_clasificada=AreaRelevante.JURIDICA, documento_id=5,
            )
        )
        servicio = _servicio(FakePublicacionRepository(), FakeDocumentoRepository(), func_repo)
        assert servicio.requiere_reextraccion(5) is False
