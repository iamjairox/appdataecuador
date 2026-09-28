"""Tests: ConsultaService (Submodulos 4.5, 4.6, 4.7) -- con fakes."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from govdata.application.dto.filtros_consulta_dto import FiltrosConsultaDTO
from govdata.application.dto.resultado_descubrimiento_dto import ResultadoDescubrimientoEntidadDTO
from govdata.application.dto.resultado_unificado_dto import (
    DocumentoResumenDTO,
    EntidadResumenDTO,
    ResultadoUnificadoDTO,
)
from govdata.application.services.cache_service import CacheService
from govdata.application.services.consulta_service import ConsultaService
from govdata.application.services.job_manager_service import JobManagerService
from govdata.domain.entities.documento import DocumentoTransparencia, EstadoDocumento, TipoArchivo
from govdata.domain.entities.entidad import Entidad
from govdata.domain.entities.funcionario import Funcionario
from govdata.domain.entities.persona import Persona
from govdata.domain.entities.publicacion import PublicacionMensual
from govdata.domain.exceptions.domain_exceptions import (
    DescargaFallidaError,
    DocumentoNoSoportadoError,
    PublicacionNoDisponibleError,
)
from govdata.domain.rules.reglas_configurables import ReglasCache
from govdata.domain.value_objects.area_relevante import AreaRelevante
from govdata.domain.value_objects.cargo import Cargo
from govdata.domain.value_objects.nombre_completo import NombreCompleto
from tests.unit.application.fakes import FakeEntidadRepository, FakePublicacionRepository
from tests.unit.application.fakes_descarga import FakeDocumentoRepositoryDescarga
from tests.unit.application.fakes_extraccion import (
    FakeDescargaPort,
    FakeDescubrimientoPort,
    FakeExtraccionPort,
    FakeFuncionarioRepositoryExtraccion,
    FakeJobRepository,
    FakePersonaRepository,
)


def _entidad() -> Entidad:
    return Entidad(id=1, nombre="Entidad X", url_transparencia="https://x/1", portal_origen="dpe")


def _publicacion() -> PublicacionMensual:
    return PublicacionMensual(id=1, entidad_id=1, mes_publicado=date(2026, 6, 1), url_item="x")


def _documento(estado: EstadoDocumento = EstadoDocumento.DESCARGADO) -> DocumentoTransparencia:
    kwargs = {
        "id": 1,
        "publicacion_id": 1,
        "tipo_archivo": TipoArchivo.PDF,
        "nombre_original": "d.pdf",
        "url_documento": "https://x/d.pdf",
        "estado": estado,
    }
    if estado == EstadoDocumento.DESCARGADO:
        kwargs.update(hash_sha256="a" * 64, tamano_bytes=100, ruta_almacenamiento="file:///d.pdf")
    return DocumentoTransparencia(**kwargs)  # type: ignore[arg-type]


def _resultado_unificado() -> ResultadoUnificadoDTO:
    return ResultadoUnificadoDTO(
        entidad=EntidadResumenDTO(id=1, nombre="Entidad X", portal_origen="dpe"),
        documento=DocumentoResumenDTO(id=1, tipo_archivo="pdf", mes_publicado=date(2026, 6, 1), hash_sha256="a" * 64, version=1, url="x"),
        funcionarios=[],
        generado_en=datetime.now(UTC),
    )


def _servicio(
    descubrimiento,
    descarga,
    extraccion,
    entidad_repo=None,
    publicacion_repo=None,
    documento_repo=None,
    funcionario_repo=None,
    persona_repo=None,
):
    publicacion_repo = publicacion_repo if publicacion_repo is not None else FakePublicacionRepository()
    documento_repo = documento_repo if documento_repo is not None else FakeDocumentoRepositoryDescarga()
    funcionario_repo = funcionario_repo if funcionario_repo is not None else FakeFuncionarioRepositoryExtraccion()
    cache_service = CacheService(
        publicacion_repository=publicacion_repo,
        documento_repository=documento_repo,
        funcionario_repository=funcionario_repo,
        reglas=ReglasCache(dias_vigencia=1),
    )
    job_manager = JobManagerService(FakeJobRepository())
    return ConsultaService(
        entidad_repository=entidad_repo or FakeEntidadRepository(),
        funcionario_repository=funcionario_repo,
        persona_repository=persona_repo if persona_repo is not None else FakePersonaRepository(),
        cache_service=cache_service,
        job_manager=job_manager,
        descubrimiento=descubrimiento,
        descarga=descarga,
        extraccion=extraccion,
    )


class TestConsultarEntidadFlujoCompleto:
    def test_flujo_feliz_completo(self) -> None:
        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(
            entidad=_entidad(), publicacion=_publicacion(), documento=_documento(EstadoDocumento.DESCUBIERTO), exito=True
        )
        descubrimiento = FakeDescubrimientoPort(resultado_descubrimiento)
        descarga = FakeDescargaPort(documento_resultado=_documento(EstadoDocumento.DESCARGADO))
        extraccion = FakeExtraccionPort(_resultado_unificado())

        servicio = _servicio(descubrimiento, descarga, extraccion)
        resultado = servicio.consultar_entidad(_entidad())

        assert resultado.entidad.nombre == "Entidad X"
        assert descubrimiento.llamadas == 1
        assert descarga.llamadas == 1
        assert extraccion.llamadas == 1

    def test_sin_publicacion_propaga_error(self) -> None:
        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(
            entidad=_entidad(), publicacion=None, documento=None, exito=False, error="sin publicacion"
        )
        servicio = _servicio(
            FakeDescubrimientoPort(resultado_descubrimiento), FakeDescargaPort(), FakeExtraccionPort(_resultado_unificado())
        )
        with pytest.raises(PublicacionNoDisponibleError):
            servicio.consultar_entidad(_entidad())

    def test_error_de_descarga_propaga(self) -> None:
        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(
            entidad=_entidad(), publicacion=_publicacion(), documento=_documento(EstadoDocumento.DESCUBIERTO), exito=True
        )
        servicio = _servicio(
            FakeDescubrimientoPort(resultado_descubrimiento),
            FakeDescargaPort(error=DescargaFallidaError("fallo de red")),
            FakeExtraccionPort(_resultado_unificado()),
        )
        with pytest.raises(DescargaFallidaError):
            servicio.consultar_entidad(_entidad())


class TestConsultarMasiva:
    def test_reutiliza_consultar_entidad_por_cada_una(self) -> None:
        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(
            entidad=_entidad(), publicacion=_publicacion(), documento=_documento(EstadoDocumento.DESCUBIERTO), exito=True
        )
        descubrimiento = FakeDescubrimientoPort(resultado_descubrimiento)
        servicio = _servicio(descubrimiento, FakeDescargaPort(documento_resultado=_documento()), FakeExtraccionPort(_resultado_unificado()))

        entidades = [
            Entidad(id=1, nombre="A", url_transparencia="https://x/1", portal_origen="dpe"),
            Entidad(id=2, nombre="B", url_transparencia="https://x/2", portal_origen="dpe"),
        ]
        resultados = servicio.consultar_masiva(entidades)

        assert len(resultados) == 2
        assert descubrimiento.llamadas == 2

    def test_un_fallo_no_detiene_el_lote(self) -> None:
        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(
            entidad=_entidad(), publicacion=None, documento=None, exito=False, error="sin publicacion"
        )
        servicio = _servicio(
            FakeDescubrimientoPort(resultado_descubrimiento), FakeDescargaPort(), FakeExtraccionPort(_resultado_unificado())
        )
        entidades = [
            Entidad(id=1, nombre="A", url_transparencia="https://x/1", portal_origen="dpe"),
            Entidad(id=2, nombre="B", url_transparencia="https://x/2", portal_origen="dpe"),
        ]
        resultados = servicio.consultar_masiva(entidades)
        assert resultados == []  # ambas fallan, pero no se lanza excepcion


class TestConsultarConFiltros:
    def test_delega_en_el_repositorio(self) -> None:
        servicio = _servicio(
            FakeDescubrimientoPort(ResultadoDescubrimientoEntidadDTO(entidad=_entidad(), publicacion=None, documento=None, exito=False)),
            FakeDescargaPort(),
            FakeExtraccionPort(_resultado_unificado()),
        )
        resultados = servicio.consultar_con_filtros(FiltrosConsultaDTO())
        assert resultados == []

    def test_descarta_silenciosamente_funcionarios_con_persona_faltante(self) -> None:
        """Si la Persona referenciada ya no existe (borrado logico, dato
        huerfano), `_a_dto` devuelve None para esa fila en vez de romper
        toda la respuesta -- coherente con la politica de "nunca detener
        el pipeline" del resto del Modulo 4."""
        funcionario_repo = FakeFuncionarioRepositoryExtraccion()
        funcionario_repo.guardar(
            Funcionario(
                persona_id=999,  # no existe en persona_repo
                entidad_id=1,
                cargo=Cargo("Director Juridico"),
                dependencia="X",
                area_clasificada=AreaRelevante.JURIDICA,
            )
        )
        servicio = _servicio(
            FakeDescubrimientoPort(ResultadoDescubrimientoEntidadDTO(entidad=_entidad(), publicacion=None, documento=None, exito=False)),
            FakeDescargaPort(),
            FakeExtraccionPort(_resultado_unificado()),
            funcionario_repo=funcionario_repo,
        )
        resultados = servicio.consultar_con_filtros(FiltrosConsultaDTO())
        assert resultados == []


class TestConsultarEntidadDocumentoNoDisponible:
    def test_descubrimiento_exitoso_sin_documento_lanza_documento_no_soportado(self) -> None:
        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(
            entidad=_entidad(), publicacion=_publicacion(), documento=None, exito=True
        )
        servicio = _servicio(
            FakeDescubrimientoPort(resultado_descubrimiento), FakeDescargaPort(), FakeExtraccionPort(_resultado_unificado())
        )
        with pytest.raises(DocumentoNoSoportadoError):
            servicio.consultar_entidad(_entidad())


def _persona_persistida(persona_repo: FakePersonaRepository, entidad_id: int) -> Persona:
    return persona_repo.guardar(
        Persona(nombre_completo=NombreCompleto(nombres="Juan", apellidos="Perez"), fingerprint="JUANPEREZ")
    )


class TestConsultarEntidadServidaDesdeCache:
    def test_cache_vigente_no_llama_descarga_ni_extraccion(self) -> None:
        publicacion_repo = FakePublicacionRepository()
        publicacion = publicacion_repo.guardar_o_actualizar(_publicacion())

        documento_repo = FakeDocumentoRepositoryDescarga()
        documento = documento_repo.guardar_o_actualizar(
            DocumentoTransparencia(
                id=1,
                publicacion_id=publicacion.id,
                tipo_archivo=TipoArchivo.PDF,
                nombre_original="d.pdf",
                url_documento="https://x/d.pdf",
                estado=EstadoDocumento.DESCARGADO,
                hash_sha256="a" * 64,
                tamano_bytes=100,
                ruta_almacenamiento="file:///d.pdf",
                descargado_en=datetime.now(UTC),
            )
        )

        persona_repo = FakePersonaRepository()
        persona = _persona_persistida(persona_repo, 1)

        funcionario_repo = FakeFuncionarioRepositoryExtraccion()
        funcionario_repo.guardar(
            Funcionario(
                persona_id=persona.id, entidad_id=1, cargo=Cargo("Director Juridico"), dependencia="X",
                area_clasificada=AreaRelevante.JURIDICA, documento_id=documento.id,
            )
        )

        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(
            entidad=_entidad(), publicacion=_publicacion(), documento=_documento(EstadoDocumento.DESCUBIERTO), exito=True
        )
        descarga = FakeDescargaPort()
        extraccion = FakeExtraccionPort(_resultado_unificado())
        servicio = _servicio(
            FakeDescubrimientoPort(resultado_descubrimiento),
            descarga,
            extraccion,
            publicacion_repo=publicacion_repo,
            documento_repo=documento_repo,
            funcionario_repo=funcionario_repo,
            persona_repo=persona_repo,
        )

        resultado = servicio.consultar_entidad(_entidad())

        assert descarga.llamadas == 0
        assert extraccion.llamadas == 0
        assert len(resultado.funcionarios) == 1
        assert resultado.funcionarios[0].nombre == persona.nombre_completo.nombres

    def test_extraccion_ya_vigente_no_vuelve_a_extraer(self) -> None:
        """Cache "por tiempo" vencido/inexistente, pero la version actual
        del documento YA tiene funcionarios extraidos (Submodulo 4.9,
        `requiere_reextraccion`) -- se reusa lo persistido sin llamar
        `ExtraccionPort` de nuevo."""
        documento_descubierto = _documento(EstadoDocumento.DESCUBIERTO)
        documento_descargado = DocumentoTransparencia(
            id=1, publicacion_id=1, tipo_archivo=TipoArchivo.PDF, nombre_original="d.pdf",
            url_documento="https://x/d.pdf", estado=EstadoDocumento.DESCARGADO,
            hash_sha256="a" * 64, tamano_bytes=100, ruta_almacenamiento="file:///d.pdf",
            descargado_en=datetime.now(UTC),
        )

        persona_repo = FakePersonaRepository()
        persona = _persona_persistida(persona_repo, 1)
        funcionario_repo = FakeFuncionarioRepositoryExtraccion()
        funcionario_repo.guardar(
            Funcionario(
                persona_id=persona.id, entidad_id=1, cargo=Cargo("Director Juridico"), dependencia="X",
                area_clasificada=AreaRelevante.JURIDICA, documento_id=1,
            )
        )

        resultado_descubrimiento = ResultadoDescubrimientoEntidadDTO(
            entidad=_entidad(), publicacion=_publicacion(), documento=documento_descubierto, exito=True
        )
        extraccion = FakeExtraccionPort(_resultado_unificado())
        servicio = _servicio(
            FakeDescubrimientoPort(resultado_descubrimiento),
            FakeDescargaPort(documento_resultado=documento_descargado),
            extraccion,
            funcionario_repo=funcionario_repo,
            persona_repo=persona_repo,
        )

        resultado = servicio.consultar_entidad(_entidad())

        assert extraccion.llamadas == 0
        assert len(resultado.funcionarios) == 1
