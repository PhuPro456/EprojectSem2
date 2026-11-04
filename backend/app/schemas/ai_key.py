from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

AIProviderName = Literal["openai", "gemini", "grok", "deepseek"]


class AIKeyCreate(BaseModel):
    provider: AIProviderName
    label: str = Field(min_length=1, max_length=80)
    api_key: str = Field(min_length=8, max_length=512)

    @field_validator("label", "api_key")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value must contain at least one non-whitespace character")
        return normalized


class AIKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: AIProviderName
    label: str
    key_hint: str
    created_at: datetime


class AIKeyVerifyResult(BaseModel):
    key_id: int
    provider: AIProviderName
    status: Literal["format_ok", "invalid_format"]
    message: str


class AIProviderRead(BaseModel):
    slug: str
    name: str
    key_prefix: str
    console_url: str
    description: str
