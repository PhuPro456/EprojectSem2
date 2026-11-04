from decimal import Decimal
from typing import Literal

from sqlalchemy import Row, Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.book import Book, Category
from app.schemas.book import BookCreate, BookStats, BookUpdate, CategoryRead

SortField = Literal["id", "title", "price", "stock"]
SortOrder = Literal["asc", "desc"]

SORT_COLUMNS = {
    "id": Book.id,
    "title": Book.title,
    "price": Book.price,
    "stock": Book.stock,
}


def normalize_category(value: str) -> str:
    return "-".join(value.casefold().split())


def build_books_query(
    *,
    keyword: str | None = None,
    category: str | None = None,
    max_price: Decimal | None = None,
    is_available: bool | None = None,
    sort_by: SortField = "id",
    order: SortOrder = "asc",
) -> Select:
    stmt = select(Book)

    if keyword:
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(Book.title.ilike(pattern), Book.author.ilike(pattern))
        )
    if category:
        stmt = stmt.where(Book.category_code == normalize_category(category))
    if max_price is not None:
        stmt = stmt.where(Book.price <= max_price)
    if is_available is True:
        stmt = stmt.where(Book.stock > 0)
    elif is_available is False:
        stmt = stmt.where(Book.stock == 0)

    column = SORT_COLUMNS[sort_by]
    direction = column.desc() if order == "desc" else column.asc()
    return stmt.order_by(direction, Book.id.asc())


def build_count_query(stmt: Select) -> Select:
    return select(func.count()).select_from(stmt.order_by(None).subquery())


def build_categories_query() -> Select:
    return (
        select(
            Category.code,
            Category.name,
            func.count(Book.id).label("book_count"),
        )
        .outerjoin(Book, Book.category_code == Category.code)
        .group_by(Category.code, Category.name)
        .order_by(Category.name)
    )


def build_stats_query() -> Select:
    return select(
        func.count(Book.id).label("total_books"),
        func.count(Book.id).filter(Book.stock > 0).label("available_books"),
        func.count(Book.id).filter(Book.stock == 0).label("out_of_stock_books"),
        func.coalesce(func.sum(Book.stock), 0).label("total_stock"),
        func.coalesce(func.sum(Book.price * Book.stock), 0).label("inventory_value"),
        func.coalesce(func.avg(Book.price), 0).label("average_price"),
    )


def stats_from_row(row: Row) -> BookStats:
    return BookStats(
        total_books=row.total_books,
        available_books=row.available_books,
        out_of_stock_books=row.out_of_stock_books,
        total_stock=int(row.total_stock),
        inventory_value=float(row.inventory_value),
        average_price=float(row.average_price),
    )


def categories_from_rows(rows: list[Row]) -> list[CategoryRead]:
    return [
        CategoryRead(code=code, name=name, book_count=book_count)
        for code, name, book_count in rows
    ]


def list_books(
    db: Session,
    *,
    skip: int,
    limit: int,
    keyword: str | None = None,
    category: str | None = None,
    max_price: Decimal | None = None,
    is_available: bool | None = None,
    sort_by: SortField = "id",
    order: SortOrder = "asc",
) -> tuple[list[Book], int]:
    stmt = build_books_query(
        keyword=keyword,
        category=category,
        max_price=max_price,
        is_available=is_available,
        sort_by=sort_by,
        order=order,
    )
    total = db.scalar(build_count_query(stmt)) or 0
    books = list(db.scalars(stmt.offset(skip).limit(limit)).all())
    return books, total


def get_book(db: Session, book_id: int) -> Book | None:
    return db.get(Book, book_id)


def get_category(db: Session, code: str) -> Category | None:
    return db.get(Category, code)


def create_book(db: Session, data: BookCreate) -> Book:
    book = Book(
        title=data.title,
        author=data.author,
        category_code=normalize_category(data.category),
        description=data.description,
        price=data.price,
        stock=data.stock,
        cover=data.cover,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book: Book, data: BookUpdate) -> Book:
    changes = data.model_dump(exclude_unset=True)
    if "category" in changes:
        book.category_code = normalize_category(changes.pop("category"))
    for field, value in changes.items():
        setattr(book, field, value)
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book: Book) -> None:
    db.delete(book)
    db.commit()
