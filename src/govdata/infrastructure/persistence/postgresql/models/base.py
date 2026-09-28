"""Base declarativa compartida por todos los modelos SQLAlchemy."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa. Todos los modelos ORM heredan de aqui."""
