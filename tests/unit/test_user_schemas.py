from datetime import datetime
import json

import pytest
from pydantic import ValidationError

from app.models import User
from app.schemas import UserCreate, UserRead


def test_user_create_validates_and_normalizes_email():
    user = UserCreate(username="alice", email="alice@EXAMPLE.COM", password="test-password")
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.password == "test-password"
    assert "test-password" not in repr(user)


@pytest.mark.parametrize(
    "values",
    [
        {"username": "alice", "email": "not-an-email", "password": "test-password"},
        {"username": "", "email": "alice@example.com", "password": "test-password"},
        {"username": "a" * 51, "email": "alice@example.com", "password": "test-password"},
        {"username": "alice", "email": "alice@example.com", "password": ""},
        {"username": "alice", "email": "alice@example.com"},
        {"email": "alice@example.com", "password": "test-password"},
        {"username": "alice", "password": "test-password"},
        {"username": "alice", "email": "a" * 64 + "@" + "b" * 32 + ".com", "password": "test-password"},
        {
            "username": "alice",
            "email": "alice@example.com",
            "password": "test-password",
            "password_hash": "injected",
        },
    ],
)
def test_user_create_rejects_invalid_input(values):
    with pytest.raises(ValidationError):
        UserCreate(**values)


def test_user_create_accepts_database_length_boundaries():
    user = UserCreate(
        username="a" * 50,
        email="a" * 64 + "@" + "b" * 31 + ".com",
        password="x",
    )
    assert len(user.username) == 50
    assert len(user.email) == 100


def test_user_create_rejects_normalized_email_over_database_length():
    with pytest.raises(ValidationError, match="Email must be at most 100 characters"):
        UserCreate(
            username="alice",
            email="a" * 64 + "@" + "b" * 32 + ".com",
            password="test-password",
        )


@pytest.mark.parametrize("created_at", [datetime(2026, 1, 1), None])
def test_user_read_from_model_excludes_secrets(created_at):
    user = User(
        id=1,
        username="alice",
        email="alice@example.com",
        password_hash="sensitive-hash",
        created_at=created_at,
    )
    result = UserRead.model_validate(user)
    assert result.model_dump() == {
        "id": 1,
        "username": "alice",
        "email": "alice@example.com",
        "created_at": created_at,
    }
    data = json.loads(result.model_dump_json())
    assert "password" not in data
    assert "password_hash" not in data
    assert "sensitive-hash" not in result.model_dump_json()
