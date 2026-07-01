import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.config import get_settings

settings = get_settings()
_hasher = PasswordHasher()  # Argon2id defaults


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """True when Argon2 parameters changed and the stored hash should be upgraded."""
    return _hasher.check_needs_rehash(password_hash)


def _create_token(subject: uuid.UUID, token_type: TokenType, expires: timedelta) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type.value,
        "iat": now,
        "exp": now + expires,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: uuid.UUID) -> str:
    return _create_token(
        subject, TokenType.ACCESS, timedelta(minutes=settings.access_token_minutes)
    )


def create_refresh_token(subject: uuid.UUID) -> str:
    return _create_token(
        subject, TokenType.REFRESH, timedelta(days=settings.refresh_token_days)
    )


def decode_token(token: str, expected_type: TokenType) -> uuid.UUID:
    """Return the subject UUID or raise jwt exceptions / ValueError on mismatch."""
    payload = jwt.decode(
        token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )
    if payload.get("type") != expected_type.value:
        raise ValueError("unexpected token type")
    return uuid.UUID(payload["sub"])
