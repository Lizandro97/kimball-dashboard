"""Database package — singleton engine, session factory, and ORM models."""

from db.engine import EngineFactory, get_engine, get_session
from db.models import (
    Base,
    DCustomer,
    DDate,
    DLocation,
    DOrder,
    DProduct,
    DSegment,
    EtlLog,
    FSales,
)

__all__ = [
    "Base",
    "DCustomer",
    "DDate",
    "DLocation",
    "DOrder",
    "DProduct",
    "DSegment",
    "EngineFactory",
    "EtlLog",
    "FSales",
    "get_engine",
    "get_session",
]
