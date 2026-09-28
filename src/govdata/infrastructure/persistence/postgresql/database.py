"""Engine y factoria de sesiones SQLAlchemy.

Este modulo es el UNICO lugar del sistema que sabe como se conecta a
PostgreSQL. Los repositorios reciben una `Session` inyectada (via el DI
Container) -- nunca crean su propio engine.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from govdata.config.settings import Settings


def crear_engine(settings: Settings) -> Engine:
    """Crea el engine de SQLAlchemy con pool configurado desde settings."""
    return create_engine(
        settings.database.dsn,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        echo=settings.database.echo_sql,
        pool_pre_ping=True,  # evita conexiones muertas en corridas largas
        future=True,
    )


def crear_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Crea la factoria de sesiones ligada a `engine`."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def sesion_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Context manager que aplica el patron Unit of Work por operacion:
    commit si todo va bien, rollback si hay excepcion, y siempre cierra.
    """
    sesion = session_factory()
    try:
        yield sesion
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()
