import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User


@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL is not set"
)
def test_module9_migration_preserves_users_and_calculations():
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    try:
        with engine.connect() as connection:
            if connection.dialect.name != "postgresql":
                pytest.fail("TEST_DATABASE_URL must point to PostgreSQL")
            transaction = connection.begin()
            try:
                schema = "test_migration_" + uuid.uuid4().hex
                connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
                sql_dir = Path(__file__).resolve().parents[2] / "sql"
                for statement in (sql_dir / "01_create_tables.sql").read_text().split(";"):
                    if statement.strip():
                        connection.execute(text(statement))
                connection.execute(text(
                    "INSERT INTO users (username, email) VALUES ('alice', 'alice@example.com')"
                ))
                connection.execute(text(
                    "INSERT INTO calculations (operation, operand_a, operand_b, result, user_id) "
                    "VALUES ('add', 2, 3, 5, 1)"
                ))

                migration = (sql_dir / "06_migrate_users_password_hash.sql").read_text()
                connection.exec_driver_sql(migration)
                connection.exec_driver_sql(migration)

                with Session(bind=connection) as session:
                    user = session.get(User, 1)
                    assert user.username == "alice"
                    assert user.email == "alice@example.com"
                    assert user.password_hash is None
                    assert user.created_at is not None
                assert connection.execute(text(
                    "SELECT user_id, result FROM calculations WHERE id = 1"
                )).one() == (1, 5.0)
                with pytest.raises(IntegrityError):
                    with connection.begin_nested():
                        connection.execute(text(
                            "INSERT INTO users (username, email) "
                            "VALUES ('alice', 'other@example.com')"
                        ))
                with pytest.raises(IntegrityError):
                    with connection.begin_nested():
                        connection.execute(text(
                            "INSERT INTO users (username, email) "
                            "VALUES ('other', 'alice@example.com')"
                        ))
                with pytest.raises(IntegrityError):
                    with connection.begin_nested():
                        connection.execute(text(
                            "INSERT INTO calculations "
                            "(operation, operand_a, operand_b, result, user_id) "
                            "VALUES ('add', 1, 1, 2, 999)"
                        ))
                connection.execute(text("DELETE FROM users WHERE id = 1"))
                assert connection.execute(text("SELECT count(*) FROM calculations")).scalar_one() == 0
            finally:
                transaction.rollback()
    finally:
        engine.dispose()
