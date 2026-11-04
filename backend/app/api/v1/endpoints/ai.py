from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DatabaseSession, get_optional_user
from app.core.ai_providers import PROVIDERS
from app.models.user import User
from app.schemas.ai import ChatRequest, ChatResponse, RecommendationResponse
from app.schemas.ai_key import AIProviderRead
from app.services.recommender import answer_chat, build_recommendations

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/providers", response_model=list[AIProviderRead])
def list_providers() -> list[AIProviderRead]:
    return [
        AIProviderRead(
            slug=provider.slug,
            name=provider.name,
            key_prefix=provider.key_prefix,
            console_url=provider.console_url,
            description=provider.description,
        )
        for provider in PROVIDERS.values()
    ]


@router.get("/recommendations", response_model=RecommendationResponse)
def recommendations(
    db: DatabaseSession,
    current_user: Annotated[User | None, Depends(get_optional_user)],
    limit: Annotated[int, Query(ge=1, le=8)] = 4,
) -> RecommendationResponse:
    books, reason = build_recommendations(db, current_user, limit=limit)
    return RecommendationResponse(reason=reason, items=books)


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: DatabaseSession,
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> ChatResponse:
    reply, suggestions, books = answer_chat(db, payload.message, current_user)
    return ChatResponse(reply=reply, suggestions=suggestions, books=books)
