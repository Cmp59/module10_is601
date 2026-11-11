import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.database import get_db, get_engine
from main import app


def test_missing_database_url(monkeypatch):
    for name in ("DATABASE_URL", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "DATABASE_HOST"):
        monkeypatch.delenv(name, raising=False)
    get_engine.cache_clear()
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        get_engine()


def test_session_uses_configured_engine(monkeypatch):
    engine = create_engine("sqlite://")
    monkeypatch.setattr("app.database.get_engine", lambda: engine)
    generator = get_db()
    session = next(generator)
    assert session.execute(text("SELECT 1")).scalar_one() == 1
    generator.close()
    engine.dispose()


def test_compose_connection_settings_escape_password(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_HOST", "db")
    monkeypatch.setenv("POSTGRES_USER", "postgres")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test@password")
    monkeypatch.setenv("POSTGRES_DB", "fastapi_db")
    engine = create_engine("sqlite://")
    urls = []
    monkeypatch.setattr("app.database.create_engine", lambda url, **kwargs: urls.append(url) or engine)
    get_engine.cache_clear()
    try:
        assert get_engine() is engine
        assert urls[0].password == "test@password"
        assert urls[0].host == "db"
    finally:
        get_engine.cache_clear()
        engine.dispose()


def test_health_checks_database(monkeypatch):
    engine = create_engine("sqlite://")
    monkeypatch.setattr("main.get_engine", lambda: engine)
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    engine.dispose()


def test_health_reports_missing_configuration(monkeypatch):
    for name in ("DATABASE_URL", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "DATABASE_HOST"):
        monkeypatch.delenv(name, raising=False)
    get_engine.cache_clear()
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"error": "Database unavailable"}


def test_health_reports_database_failure(monkeypatch):
    engine = create_engine("sqlite:///nonexistent_directory/database.db")
    monkeypatch.setattr("main.get_engine", lambda: engine)
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"error": "Database unavailable"}
    engine.dispose()


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL is not set"
)
def test_postgresql_connection():
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
            assert connection.dialect.name == "postgresql"
    finally:
        engine.dispose()
