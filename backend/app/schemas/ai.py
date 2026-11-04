from pydantic import BaseModel, Field

from app.schemas.book import BookRead


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)


class ChatResponse(BaseModel):
    reply: str
    suggestions: list[str]
    books: list[BookRead]


class RecommendationResponse(BaseModel):
    reason: str
    items: list[BookRead]
