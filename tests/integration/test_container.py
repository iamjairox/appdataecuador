"""Tests de integracion: Container (DI) -- metodos del Modulo 2.

`Container.engine`/`session_factory` normalmente construyen una conexion
real a PostgreSQL (`cached_property`, perezosa). Para poder probar el
wiring sin una base real, se pre-carga `session_factory` directamente en
el `__dict__` de la instancia ANTES de usarla -- `cached_property`
respeta cualquier valor ya presente ahi y nunca ejecuta el computo real.
Esto prueba el grafo de dependencias real (`descubrir_y_persistir_entidades`,
`crear_pipeline_descubrimiento`) sin necesitar PostgreSQL.
"""

from __future__ import annotations

from sqlalchemy.orm import sessionmaker

from govdata.config.container import Container
from govdata.config.settings import Settings, reset_settings_cache


def _container_con_sqlite(sqlite_engine_multihilo, servidor_fixtures_dpe) -> Container:
    settings = Settings(
        APP_ENV="test",
        database={"nombre": "no_se_usa"},
        scraping={
            "url_origen_dpe": servidor_fixtures_dpe.url_origen,
            "intervalo_minimo_segundos": 0.0,
            "max_reintentos": 1,
            "backoff_base_segundos": 0.01,
            "concurrencia_maxima": 2,
        },
    )
    container = Container(settings=settings)
    container.__dict__["session_factory"] = sessionmaker(bind=sqlite_engine_multihilo, future=True)
    return container


def test_descubrir_y_persistir_entidades(sqlite_engine_multihilo, servidor_fixtures_dpe) -> None:
    container = _container_con_sqlite(sqlite_engine_multihilo, servidor_fixtures_dpe)

    entidades = container.descubrir_y_persistir_entidades()

    assert len(entidades) == 4
    assert all(e.id is not None for e in entidades)


def test_crear_pipeline_descubrimiento_ejecuta_extremo_a_extremo(
    sqlite_engine_multihilo, servidor_fixtures_dpe
) -> None:
    container = _container_con_sqlite(sqlite_engine_multihilo, servidor_fixtures_dpe)

    entidades = container.descubrir_y_persistir_entidades()
    orquestador = container.crear_pipeline_descubrimiento()
    resumen = orquestador.ejecutar(entidades)

    assert resumen.total_entidades == 4
    assert resumen.documentos_encontrados >= 1  # al menos UNAE (establishment_id=1920) debe encontrarse


def test_rate_limiter_es_compartido_entre_llamadas(sqlite_engine_multihilo, servidor_fixtures_dpe) -> None:
    container = _container_con_sqlite(sqlite_engine_multihilo, servidor_fixtures_dpe)
    assert container.rate_limiter is container.rate_limiter


def teardown_module() -> None:
    reset_settings_cache()
