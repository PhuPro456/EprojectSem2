from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DatabaseSession, get_current_user
from app.crud import book as book_crud
from app.crud import review as review_crud
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewList, ReviewRead

router = APIRouter(prefix="/books/{book_id}/reviews", tags=["reviews"])


def _ensure_book(db: DatabaseSession, book_id: int) -> None:
    if book_crud.get_book(db, book_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found",
        )


@router.get("", response_model=ReviewList)
def list_reviews(book_id: int, db: DatabaseSession) -> ReviewList:
    _ensure_book(db, book_id)
    reviews = review_crud.list_reviews(db, book_id)
    return ReviewList(
        summary=review_crud.build_summary(reviews),
        items=reviews,
    )


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_review(
    book_id: int,
    payload: ReviewCreate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Review:
    _ensure_book(db, book_id)
    return review_crud.create_review(db, book_id, current_user, payload)
