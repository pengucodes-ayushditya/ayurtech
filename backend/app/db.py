import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import normalize_database_url

DATABASE_URL = normalize_database_url(
    os.getenv("DATABASE_URL", "sqlite:///./ayurtech.db")
)
if os.getenv("APP_ENV") == "production" and not DATABASE_URL.startswith("postgresql+"):
    raise RuntimeError("Production requires an explicit PostgreSQL DATABASE_URL")
engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    ),
    pool_pre_ping=True,
)
if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as db:
        yield db
