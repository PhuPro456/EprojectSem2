from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Loaded relative to the current directory, so both "python run.py" from
        # the project root and "uvicorn app.main:app" from backend/ find the file.
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    secret_key: SecretStr
    access_token_expire_minutes: int = 30
    algorithm: Literal["HS256"] = "HS256"

    # Demo administrator created on first startup against a persistent database.
    seed_admin: bool = True
    admin_email: str = "admin@bookstorepro.com"
    admin_password: str = "admin-password-123"
    admin_name: str = "Store Administrator"

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return value

    @field_validator("access_token_expire_minutes")
    @classmethod
    def validate_token_expiration(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()