"""
SQLAlchemy engine + session factory. Plain, synchronous SQLAlchemy on
purpose — FastAPI runs it in a threadpool automatically, and async SQLAlchemy
adds a layer of complexity (async drivers, await everywhere) that isn't
worth it for a project of this size and traffic.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Creates all tables if they don't exist. Called once on startup —
    fine for a local portfolio project; a real deployment would use Alembic
    migrations instead."""
    from backend.db import models  # noqa: F401 — ensures models are registered
    Base.metadata.create_all(bind=engine)
