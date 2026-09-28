"""Tests de integracion: Container (DI) -- metodos del Modulo 4.

Mismo truco que `test_container_descarga.py`: se pre-carga `session_factory`
en el `__dict__` para evitar PostgreSQL real. `crear_consulta_service`
construye un `DpeEntidadWorker` real, pero su `BrowserManager` es
perezoso (el navegador solo se lanza en el primer `procesar()`, ver
`dpe_entidad_worker.py`) -- construirlo aqui NO requiere Playwright activo.
"""

from __future__ import annotations

from sqlalchemy.orm import sessionmaker

from govdata.application.services.consulta_service import ConsultaService
from govdata.application.services.parser_factory import ParserFactory
from govdata.config.container import Container
from govdata.config.settings import Settings, reset_settings_cache
from govdata.domain.rules.reglas_configurables import RuleEngine
from govdata.infrastructure.persistence.postgresql.models.entidad_model import EntidadModel


def _container(sqlite_engine_multihilo, directorio_storage_temporal) -> Container:
    settings = Settings(
        APP_ENV="test",
        database={"nombre": "no_se_usa"},
        storage={"backend": "local", "ruta_local": directorio_storage_temporal},
    )
    container = Container(settings=settings)
    container.__dict__["session_factory"] = sessionmaker(bind=sqlite_engine_multihilo, future=True)
    return container


def test_rule_engine_es_cacheado_y_carga_las_reglas_reales(
    sqlite_engine_multihilo, directorio_storage_temporal
) -> None:
    container = _container(sqlite_engine_multihilo, directorio_storage_temporal)
    assert isinstance(container.rule_engine, RuleEngine)
    assert container.rule_engine is container.rule_engine  # cached_property


def test_parser_factory_incluye_los_cuatro_formatos(sqlite_engine_multihilo, directorio_storage_temporal) -> None:
    from govdata.domain.entities.documento import TipoArchivo

    container = _container(sqlite_engine_multihilo, directorio_storage_temporal)
    assert isinstance(container.parser_factory, ParserFactory)
    for tipo in (TipoArchivo.PDF, TipoArchivo.XLSX, TipoArchivo.XLS, TipoArchivo.CSV):
        assert container.parser_factory.obtener_parser(tipo) is not None


def test_buscar_entidad_por_nombre(sqlite_engine_multihilo, directorio_storage_temporal) -> None:
    container = _container(sqlite_engine_multihilo, directorio_storage_temporal)
    with container.nueva_sesion() as sesion:
        sesion.add(EntidadModel(nombre="Ministerio de Prueba", url_transparencia="https://x/1", portal_origen="dpe"))

    with container.nueva_sesion() as sesion:
        encontrada = container.buscar_entidad_por_nombre(sesion, "Ministerio")
        assert encontrada is not None
        assert encontrada.nombre == "Ministerio de Prueba"

        no_encontrada = container.buscar_entidad_por_nombre(sesion, "No Existe")
        assert no_encontrada is None


def test_crear_consulta_service_arma_el_grafo_completo(sqlite_engine_multihilo, directorio_storage_temporal) -> None:
    container = _container(sqlite_engine_multihilo, directorio_storage_temporal)
    with container.nueva_sesion() as sesion:
        servicio = container.crear_consulta_service(sesion)
        assert isinstance(servicio, ConsultaService)
        # Wiring real de punta a punta: una consulta por filtros (solo
        # lectura) contra una base vacia no debe lanzar ninguna excepcion.
        from govdata.application.dto.filtros_consulta_dto import FiltrosConsultaDTO

        assert servicio.consultar_con_filtros(FiltrosConsultaDTO()) == []


def teardown_module() -> None:
    reset_settings_cache()
