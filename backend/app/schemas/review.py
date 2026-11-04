from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Sentiment = Literal["positive", "neutral", "negative"]


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=3, max_length=2000)

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("Review text must contain at least 3 characters")
        return normalized


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    author_name: str
    rating: int
    text: str
    sentiment: Sentiment
    keywords: list[str]
    created_at: datetime


class ReviewSummary(BaseModel):
    total: int
    positive: int
    neutral: int
    negative: int
    average_rating: float


class ReviewList(BaseModel):
    summary: ReviewSummary
    items: list[ReviewRead]


class RecentReviewRead(ReviewRead):
    book_title: str


class KeywordCount(BaseModel):
    keyword: str
    count: int


class ReviewDashboard(BaseModel):
    summary: ReviewSummary
    positive_keywords: list[KeywordCount]
    negative_keywords: list[KeywordCount]
    items: list[RecentReviewRead]
