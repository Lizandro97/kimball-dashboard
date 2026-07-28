"""Singleton engine + session factory from environment variables."""

from __future__ import annotations

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lizandro:148256@localhost/superstore")


class EngineFactory:
    """Singleton engine and session factory."""

    _engine: Engine | None = None
    _session_factory: sessionmaker[Session] | None = None

    @classmethod
    def engine(cls) -> Engine:
        if cls._engine is None:
            cls._engine = create_engine(
                _DATABASE_URL,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
            )
        return cls._engine

    @classmethod
    def session_factory(cls) -> sessionmaker[Session]:
        if cls._session_factory is None:
            cls._session_factory = sessionmaker(bind=cls.engine())
        return cls._session_factory

    @classmethod
    def session(cls) -> Session:
        return cls.session_factory()()


def get_engine() -> Engine:
    return EngineFactory.engine()


def get_session() -> Generator[Session, None, None]:
    session = EngineFactory.session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
