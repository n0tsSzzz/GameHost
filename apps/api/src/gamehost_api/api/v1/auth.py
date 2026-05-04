from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from gamehost_api.core.config import Settings, get_settings
from gamehost_api.core.security import decode_access_token
from gamehost_api.db.base import get_session
from gamehost_api.db.models import User
from gamehost_api.domain.auth import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidRefreshToken,
    get_user_by_id,
    login_user,
    register_user,
    revoke_refresh_token,
    rotate_refresh_token,
)
from gamehost_api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)

BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
RefreshCookieDep = Annotated[str | None, Cookie(alias="refresh_token")]


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client is not None else None


def _set_refresh_cookie(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(
        settings.refresh_cookie_name,
        token,
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(settings.refresh_cookie_name, path="/api/v1/auth")


async def get_current_user(
    credentials: BearerCredentials,
    session: SessionDep,
    settings: SettingsDep,
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        user_id = decode_access_token(credentials.credentials, settings)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
    user = await get_user_by_id(session, UUID(str(user_id)))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active")
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: SessionDep) -> User:
    try:
        return await register_user(session, payload.email, payload.password)
    except EmailAlreadyRegistered as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from exc


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
) -> TokenResponse:
    try:
        _user, access, refresh = await login_user(
            session,
            settings,
            payload.email,
            payload.password,
            request.headers.get("user-agent"),
            _client_ip(request),
        )
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from exc
    _set_refresh_cookie(response, settings, refresh)
    return TokenResponse(access=access)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
    refresh_cookie: RefreshCookieDep = None,
) -> TokenResponse:
    if refresh_cookie is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )
    try:
        _user, access, new_refresh = await rotate_refresh_token(
            session,
            settings,
            refresh_cookie,
            request.headers.get("user-agent"),
            _client_ip(request),
        )
    except InvalidRefreshToken as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc
    _set_refresh_cookie(response, settings, new_refresh)
    return TokenResponse(access=access)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
    refresh_cookie: RefreshCookieDep = None,
) -> None:
    if refresh_cookie is not None:
        await revoke_refresh_token(session, refresh_cookie)
    _clear_refresh_cookie(response, settings)


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
