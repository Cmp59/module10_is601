import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Base, User
from app.security import verify_password
from main import app


@pytest.fixture(params=["new", "migrated"])
def user_api(request):
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not set")
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            if connection.dialect.name != "postgresql":
                pytest.fail("TEST_DATABASE_URL must point to PostgreSQL")
            transaction = connection.begin()
            try:
                schema = "test_user_api_" + uuid.uuid4().hex
                connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
                if request.param == "new":
                    Base.metadata.create_all(connection)
                else:
                    sql_dir = Path(__file__).resolve().parents[2] / "sql"
                    for statement in (sql_dir / "01_create_tables.sql").read_text().split(";"):
                        if statement.strip():
                            connection.execute(text(statement))
                    connection.exec_driver_sql(
                        (sql_dir / "06_migrate_users_password_hash.sql").read_text()
                    )

                def override_get_db():
                    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                        yield session

                app.dependency_overrides[get_db] = override_get_db
                with TestClient(app) as client:
                    yield client, connection
            finally:
                app.dependency_overrides.pop(get_db, None)
                transaction.rollback()
    finally:
        engine.dispose()


def test_create_user_hashes_password_and_returns_safe_response(user_api):
    client, connection = user_api
    response = client.post("/users", json={
        "username": "alice", "email": "alice@EXAMPLE.COM", "password": "test-password"
    })
    assert response.status_code == 201
    data = response.json()
    assert set(data) == {"id", "username", "email", "created_at"}
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert data["created_at"] is not None
    assert "test-password" not in response.text

    with Session(bind=connection) as session:
        user = session.get(User, data["id"])
        assert user is not None
        assert user.password_hash != "test-password"
        assert user.password_hash.startswith("$argon2id$")
        assert verify_password("test-password", user.password_hash)
        assert not verify_password("wrong-password", user.password_hash)


@pytest.mark.parametrize(
    "duplicate",
    [
        {"username": "alice", "email": "other@example.com", "password": "test-password"},
        {"username": "other", "email": "alice@example.com", "password": "test-password"},
    ],
)
def test_duplicate_user_is_rejected(user_api, duplicate):
    client, connection = user_api
    first = {"username": "alice", "email": "alice@example.com", "password": "test-password"}
    assert client.post("/users", json=first).status_code == 201
    response = client.post("/users", json=duplicate)
    assert response.status_code == 409
    assert response.json() == {"error": "Username or email already exists"}
    assert connection.execute(select(func.count()).select_from(User)).scalar_one() == 1


@pytest.mark.parametrize(
    "body",
    [
        {"username": "alice", "email": "invalid-email", "password": "test-password"},
        {"username": "alice", "email": "alice@example.com", "password": ""},
        {"username": "alice", "email": "alice@example.com"},
        {"username": "", "email": "alice@example.com", "password": "test-password"},
    ],
)
def test_invalid_user_is_not_saved(user_api, body):
    client, connection = user_api
    response = client.post("/users", json=body)
    assert response.status_code == 400
    assert "test-password" not in response.text
    assert connection.execute(select(func.count()).select_from(User)).scalar_one() == 0


def test_legacy_user_is_preserved_when_creating_user(user_api):
    client, connection = user_api
    connection.execute(text(
        "INSERT INTO users (username, email) VALUES ('legacy', 'legacy@example.com')"
    ))
    response = client.post("/users", json={
        "username": "alice", "email": "alice@example.com", "password": "test-password"
    })
    assert response.status_code == 201
    with Session(bind=connection) as session:
        legacy = session.scalar(select(User).where(User.username == "legacy"))
        assert legacy is not None
        assert legacy.password_hash is None
