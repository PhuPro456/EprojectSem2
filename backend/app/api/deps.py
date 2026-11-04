from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.db.session_async import get_async_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", auto_error=False
)
DatabaseSession = Annotated[Session, Depends(get_db)]
AsyncDatabaseSession = Annotated[AsyncSession, Depends(get_async_db)]


def _user_from_token(token: str, db: Session) -> User | None:
    try:
        settings = get_settings()
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
        )
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.isdecimal():
            return None
    except jwt.InvalidTokenError:
        return None

    user = db.get(User, int(subject))
    if user is None or not user.is_active:
        return None
    return user


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DatabaseSession,
) -> User:
    user = _user_from_token(token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_optional_user(
    token: Annotated[str | None, Depends(optional_oauth2_scheme)],
    db: DatabaseSession,
) -> User | None:
    if not token:
        return None
    return _user_from_token(token, db)


def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return current_user