from typing import Annotated

import jwt
from fastapi import APIRouter, Cookie, HTTPException, Response, status

from app.api.deps import CurrentUser, DbSession
from app.config import get_settings
from app.core.exceptions import EmailAlreadyExists, InvalidCredentials
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.schemas.auth import AccessToken, UserLogin, UserOut, UserRegister
from app.services.auth import AuthService

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, user_id) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=create_refresh_token(user_id),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_days * 86400,
        path="/api/v1/auth",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: DbSession) -> UserOut:
    try:
        user = AuthService(db).register(data)
    except EmailAlreadyExists as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from exc
    return UserOut.model_validate(user)


@router.post("/login", response_model=AccessToken)
def login(data: UserLogin, db: DbSession, response: Response) -> AccessToken:
    try:
        user = AuthService(db).authenticate(data.email, data.password)
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        ) from exc
    _set_refresh_cookie(response, user.id)
    return AccessToken(access_token=create_access_token(user.id))


@router.post("/refresh", response_model=AccessToken)
def refresh(
    db: DbSession,
    refresh_token: Annotated[str | None, Cookie(alias=settings.refresh_cookie_name)] = None,
) -> AccessToken:
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token"
        )
    try:
        user_id = decode_token(refresh_token, TokenType.REFRESH)
    except (jwt.InvalidTokenError, ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc
    return AccessToken(access_token=create_access_token(user_id))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(settings.refresh_cookie_name, path="/api/v1/auth")


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser) -> UserOut:
    return UserOut.model_validate(current_user)
