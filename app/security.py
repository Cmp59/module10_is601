import logging

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError


logger = logging.getLogger(__name__)
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password must not be empty")
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str | None) -> bool:
    if stored_hash is None:
        return False
    try:
        return password_hasher.verify(password, stored_hash)
    except UnknownHashError:
        logger.error("Stored password hash has an unsupported format")
        return False
