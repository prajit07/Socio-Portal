from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


def _build_engine():
    url = settings.DATABASE_URL
    connect_args: dict = {}
    # Force psycopg3 driver (matches installed `psycopg[binary]` package).
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    # Neon Postgres requires SSL. Belt-and-braces: enforce sslmode=require even if missing.
    if url.startswith("postgresql") and "sslmode=" not in url:
        url = url + ("&" if "?" in url else "?") + "sslmode=require"

    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args=connect_args or {},
        future=True,
    )


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
