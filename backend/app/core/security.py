import base64
import hashlib
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import jwt
from cryptography.fernet import Fernet
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


@lru_cache
def get_fernet() -> Fernet:
    """Derive a stable Fernet key from SECRET_KEY.

    The encryption key lives in the environment, never in the database, so a
    leaked database dump does not expose the stored AI provider keys.
    """
    digest = hashlib.sha256(
        get_settings().secret_key.get_secret_value().encode("utf-8")
    ).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value: str) -> str:
    return get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    return get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": subject, "exp": expires_at},
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )