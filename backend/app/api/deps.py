from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DatabaseSession,
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        settings = get_settings()
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
        )
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.isdecimal():
            raise unauthorized
    except jwt.InvalidTokenError as exc:
        raise unauthorized from exc

    user = db.get(User, int(subject))
    if user is None or not user.is_active:
        raise unauthorized
    return user


def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return current_user
