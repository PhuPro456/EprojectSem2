from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=150)
    category: str = Field(min_length=1, max_length=50)
    description: str = Field(default="", max_length=2000)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(ge=0)
    cover: str = Field(default="", max_length=255)

    @field_validator("title", "author", "category")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value must contain at least one non-whitespace character")
        return normalized


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    author: str | None = Field(default=None, min_length=1, max_length=150)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=2000)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    cover: str | None = Field(default=None, max_length=255)

    @field_validator("title", "author", "category")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value must contain at least one non-whitespace character")
        return normalized


class BookRead(BookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    # JSON numbers for clients; the Numeric column keeps exact storage precision.
    price: float

    @computed_field
    @property
    def is_available(self) -> bool:
        return self.stock > 0


class PaginatedBooks(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[BookRead]


class BookStats(BaseModel):
    total_books: int
    available_books: int
    out_of_stock_books: int
    total_stock: int
    inventory_value: float
    average_price: float


class CategoryRead(BaseModel):
    code: str
    name: str
    book_count: int
