from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import DatabaseSession, get_current_admin
from app.crud import book as crud
from app.crud.book import SortField, SortOrder
from app.models.book import Book
from app.schemas.book import (
    BookCreate,
    BookRead,
    BookStats,
    BookUpdate,
    CategoryRead,
    PaginatedBooks,
)

router = APIRouter(prefix="/books", tags=["books"])


def _ensure_category(db: Session, category: str) -> str:
    code = crud.normalize_category(category)
    if crud.get_category(db, code) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unknown category: {category}",
        )
    return code


def _get_book_or_404(db: Session, book_id: int) -> Book:
    book = crud.get_book(db, book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found",
        )
    return book


# Static routes must stay above GET /books/{book_id}.
@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: DatabaseSession) -> list[CategoryRead]:
    rows = db.execute(crud.build_categories_query()).all()
    return crud.categories_from_rows(list(rows))


@router.get("/stats", response_model=BookStats)
def read_stats(db: DatabaseSession) -> BookStats:
    row = db.execute(crud.build_stats_query()).one()
    return crud.stats_from_row(row)


@router.get("", response_model=PaginatedBooks)
def list_books(
    db: DatabaseSession,
    keyword: Annotated[
        str | None, Query(max_length=100, description="Match title or author")
    ] = None,
    category: Annotated[
        str | None, Query(max_length=50, description="Category code or name")
    ] = None,
    max_price: Annotated[Decimal | None, Query(ge=0)] = None,
    is_available: Annotated[bool | None, Query()] = None,
    sort_by: Annotated[SortField, Query()] = "id",
    order: Annotated[SortOrder, Query()] = "asc",
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=50)] = 12,
) -> PaginatedBooks:
    books, total = crud.list_books(
        db,
        skip=skip,
        limit=limit,
        keyword=keyword,
        category=category,
        max_price=max_price,
        is_available=is_available,
        sort_by=sort_by,
        order=order,
    )
    return PaginatedBooks(total=total, skip=skip, limit=limit, items=books)


@router.post(
    "",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
def create_book(payload: BookCreate, db: DatabaseSession) -> Book:
    _ensure_category(db, payload.category)
    return crud.create_book(db, payload)


@router.get("/{book_id}", response_model=BookRead)
def read_book(book_id: int, db: DatabaseSession) -> Book:
    return _get_book_or_404(db, book_id)


@router.patch(
    "/{book_id}",
    response_model=BookRead,
    dependencies=[Depends(get_current_admin)],
)
def update_book(
    book_id: int,
    payload: BookUpdate,
    db: DatabaseSession,
) -> Book:
    book = _get_book_or_404(db, book_id)
    if payload.category is not None:
        _ensure_category(db, payload.category)
    return crud.update_book(db, book, payload)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
def delete_book(book_id: int, db: DatabaseSession) -> None:
    crud.delete_book(db, _get_book_or_404(db, book_id))
