from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str | None = None):
    url = database_url or os.getenv("DATABASE_URL", "sqlite+pysqlite:///./edunova_dev.db")
    kwargs = {"pool_pre_ping": True}
    if url.startswith("postgresql"):
        kwargs.update(
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT_SECONDS", "10")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800")),
            connect_args={"connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "5"))},
        )
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def build_session_factory(engine=None):
    engine = engine or build_engine()
    return sessionmaker(bind=engine, expire_on_commit=False)
