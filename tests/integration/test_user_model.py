import os
import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, User


@pytest.fixture(params=["sqlite", "postgresql"])
def user_session(request):
    if request.param == "postgresql":
        database_url = os.environ.get("TEST_DATABASE_URL")
        if not database_url:
            pytest.skip("TEST_DATABASE_URL is not set")
    else:
        database_url = "sqlite://"

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                if request.param == "postgresql":
                    if connection.dialect.name != "postgresql":
                        pytest.fail("TEST_DATABASE_URL must point to PostgreSQL")
                    schema = "test_users_" + uuid.uuid4().hex
                    connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                    connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
                Base.metadata.create_all(connection)
                with Session(bind=connection) as session:
                    yield session
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def test_user_has_id_and_creation_timestamp(user_session):
    user = User(username="alice", email="alice@example.com", password_hash="test-hash")
    user_session.add(user)
    user_session.flush()
    assert user.id is not None
    assert isinstance(user.created_at, datetime)
    assert user_session.get(User, user.id).password_hash == "test-hash"


@pytest.mark.parametrize(
    ("username", "email"),
    [
        ("alice", "other@example.com"),
        ("other", "alice@example.com"),
    ],
)
def test_usernames_and_emails_are_unique(user_session, username, email):
    user_session.add(
        User(username="alice", email="alice@example.com", password_hash="test-hash")
    )
    user_session.flush()
    with pytest.raises(IntegrityError):
        with user_session.begin_nested():
            user_session.add(
                User(username=username, email=email, password_hash="test-hash")
            )
            user_session.flush()


@pytest.mark.parametrize("missing", ["username", "email", "password_hash"])
def test_required_user_fields_cannot_be_null(user_session, missing):
    values = {"username": "alice", "email": "alice@example.com", "password_hash": "test-hash"}
    values[missing] = None
    with pytest.raises(IntegrityError):
        with user_session.begin_nested():
            user_session.add(User(**values))
            user_session.flush()
