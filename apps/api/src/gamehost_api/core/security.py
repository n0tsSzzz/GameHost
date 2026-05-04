from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import cast
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from gamehost_api.core.config import Settings

ALGORITHM = "HS256"
_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def create_access_token(user_id: UUID, settings: Settings) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    return cast(
        str,
        jwt.encode(
            {"sub": str(user_id), "exp": expires_at, "typ": "access"},
            settings.jwt_secret,
            algorithm=ALGORITHM,
        ),
    )


def decode_access_token(token: str, settings: Settings) -> UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid access token") from exc
    if payload.get("typ") != "access":
        raise ValueError("Invalid token type")
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise ValueError("Missing token subject")
    return UUID(subject)


def create_refresh_token() -> str:
    return token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return _password_hasher.hash(token)


def verify_refresh_token(token: str, token_hash: str) -> bool:
    return verify_password(token, token_hash)
