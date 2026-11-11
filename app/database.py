import os
from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL
from sqlalchemy.orm import Session


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    database_url: str | URL | None = os.environ.get("DATABASE_URL")
    if not database_url:
        names = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "DATABASE_HOST")
        if not all(os.environ.get(name) for name in names):
            raise RuntimeError("DATABASE_URL or PostgreSQL connection settings must be set")
        database_url = URL.create(
            "postgresql+psycopg",
            username=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host=os.environ["DATABASE_HOST"],
            port=5432,
            database=os.environ["POSTGRES_DB"],
        )
    return create_engine(database_url, pool_pre_ping=True)


def get_db() -> Iterator[Session]:
    with Session(get_engine()) as session:
        yield session
