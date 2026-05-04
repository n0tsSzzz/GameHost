from datetime import UTC, datetime, timedelta
from uuid import UUID

from gamehost_api.core.config import Settings
from gamehost_api.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
    verify_refresh_token,
)
from gamehost_api.db.models import RefreshToken, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AuthError(Exception):
    pass


class EmailAlreadyRegistered(AuthError):
    pass


class InvalidCredentials(AuthError):
    pass


class InvalidRefreshToken(AuthError):
    pass


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.get(User, user_id)


async def register_user(session: AsyncSession, email: str, password: str) -> User:
    existing = await get_user_by_email(session, email)
    if existing is not None:
        raise EmailAlreadyRegistered
    user = User(email=email.lower(), password_hash=hash_password(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def login_user(
    session: AsyncSession,
    settings: Settings,
    email: str,
    password: str,
    user_agent: str | None,
    ip: str | None,
) -> tuple[User, str, str]:
    user = await get_user_by_email(session, email)
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise InvalidCredentials

    refresh = create_refresh_token()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
            user_agent=user_agent,
            ip=ip,
        ),
    )
    await session.commit()
    return user, create_access_token(user.id, settings), refresh


async def rotate_refresh_token(
    session: AsyncSession,
    settings: Settings,
    refresh_token: str,
    user_agent: str | None,
    ip: str | None,
) -> tuple[User, str, str]:
    now = datetime.now(UTC)
    result = await session.execute(
        select(RefreshToken, User)
        .join(User, RefreshToken.user_id == User.id)
        .where(RefreshToken.revoked_at.is_(None), RefreshToken.expires_at > now)
    )
    for stored_token, user in result.all():
        if verify_refresh_token(refresh_token, stored_token.token_hash):
            stored_token.revoked_at = now
            new_refresh = create_refresh_token()
            session.add(
                RefreshToken(
                    user_id=user.id,
                    token_hash=hash_refresh_token(new_refresh),
                    expires_at=now + timedelta(days=settings.refresh_token_days),
                    user_agent=user_agent,
                    ip=ip,
                ),
            )
            await session.commit()
            return user, create_access_token(user.id, settings), new_refresh
    raise InvalidRefreshToken


async def revoke_refresh_token(session: AsyncSession, refresh_token: str) -> None:
    now = datetime.now(UTC)
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.revoked_at.is_(None), RefreshToken.expires_at > now)
    )
    for stored_token in result.scalars():
        if verify_refresh_token(refresh_token, stored_token.token_hash):
            stored_token.revoked_at = now
            await session.commit()
            return
