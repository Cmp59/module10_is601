import logging

import pytest

from app.security import hash_password, verify_password


def test_hash_and_verify_password():
    password = "test-password"
    stored_hash = hash_password(password)

    assert stored_hash.startswith("$argon2id$")
    assert password not in stored_hash
    assert len(stored_hash) <= 255
    assert verify_password(password, stored_hash) is True
    assert verify_password("wrong-password", stored_hash) is False


def test_hashes_use_unique_salts():
    first = hash_password("test-password")
    second = hash_password("test-password")
    assert first != second
    assert verify_password("test-password", first)
    assert verify_password("test-password", second)


def test_empty_password_cannot_be_hashed():
    with pytest.raises(ValueError, match="must not be empty"):
        hash_password("")


def test_legacy_user_without_hash_cannot_verify():
    assert verify_password("test-password", None) is False


@pytest.mark.parametrize("invalid_hash", ["", "not-a-hash"])
def test_unrecognized_hash_is_logged_and_rejected(invalid_hash, caplog):
    with caplog.at_level(logging.ERROR, logger="app.security"):
        assert verify_password("test-password", invalid_hash) is False
    assert "unsupported format" in caplog.text
    assert "test-password" not in caplog.text
    assert "not-a-hash" not in caplog.text


def test_malformed_argon2_hash_is_rejected():
    assert verify_password("test-password", "$argon2id$invalid") is False
