"""Shared declarative base for all ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class used by SQLAlchemy's framework-independent ORM."""

