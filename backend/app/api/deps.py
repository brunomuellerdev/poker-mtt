from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import TokenType, decode_token
from app.db.models import User
from app.db.session import get_db
from app.repositories.user import UserRepository

_bearer = HTTPBearer(auto_error=True)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> User:
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_token(credentials.credentials, TokenType.ACCESS)
    except (jwt.InvalidTokenError, ValueError, KeyError) as exc:
        raise invalid from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise invalid
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
