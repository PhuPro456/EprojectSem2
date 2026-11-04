from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AsyncDatabaseSession, get_current_admin
from app.crud import book as crud
from app.crud.book import SortField, SortOrder
from app.models.book import Book, Category
from app.schemas.book import (
    BookCreate,
    BookRead,
    BookStats,
    BookUpdate,
    CategoryRead,
    PaginatedBooks,
)

router = APIRouter(prefix="/books-async", tags=["books-async"])


async def _ensure_category(db: AsyncSession, category: str) -> str:
    code = crud.normalize_category(category)
    if await db.get(Category, code) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unknown category: {category}",
        )
    return code


async def _get_book_or_404(db: AsyncSession, book_id: int) -> Book:
    book = await db.get(Book, book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} not found",
        )
    return book


# Static routes must stay above GET /books-async/{book_id}.
@router.get("/categories", response_model=list[CategoryRead])
async def list_categories(db: AsyncDatabaseSession) -> list[CategoryRead]:
    rows = (await db.execute(crud.build_categories_query())).all()
    return crud.categories_from_rows(list(rows))


@router.get("/stats", response_model=BookStats)
async def read_stats(db: AsyncDatabaseSession) -> BookStats:
    row = (await db.execute(crud.build_stats_query())).one()
    return crud.stats_from_row(row)


@router.get("", response_model=PaginatedBooks)
async def list_books(
    db: AsyncDatabaseSession,
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
    stmt = crud.build_books_query(
        keyword=keyword,
        category=category,
        max_price=max_price,
        is_available=is_available,
        sort_by=sort_by,
        order=order,
    )
    total = await db.scalar(crud.build_count_query(stmt)) or 0
    books = list((await db.scalars(stmt.offset(skip).limit(limit))).all())
    return PaginatedBooks(total=total, skip=skip, limit=limit, items=books)


@router.post(
    "",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def create_book(payload: BookCreate, db: AsyncDatabaseSession) -> Book:
    category_code = await _ensure_category(db, payload.category)
    book = Book(
        title=payload.title,
        author=payload.author,
        category_code=category_code,
        description=payload.description,
        price=payload.price,
        stock=payload.stock,
        cover=payload.cover,
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book


@router.get("/{book_id}", response_model=BookRead)
async def read_book(book_id: int, db: AsyncDatabaseSession) -> Book:
    return await _get_book_or_404(db, book_id)


@router.patch(
    "/{book_id}",
    response_model=BookRead,
    dependencies=[Depends(get_current_admin)],
)
async def update_book(
    book_id: int,
    payload: BookUpdate,
    db: AsyncDatabaseSession,
) -> Book:
    book = await _get_book_or_404(db, book_id)
    changes = payload.model_dump(exclude_unset=True)
    if "category" in changes:
        book.category_code = await _ensure_category(db, changes.pop("category"))
    for field, value in changes.items():
        setattr(book, field, value)
    await db.commit()
    await db.refresh(book)
    return book


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
async def delete_book(book_id: int, db: AsyncDatabaseSession) -> None:
    book = await _get_book_or_404(db, book_id)
    await db.delete(book)
    await db.commit()
