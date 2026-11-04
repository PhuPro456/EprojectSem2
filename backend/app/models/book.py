from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Category(Base):
    __tablename__ = "categories"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint("stock >= 0", name="non_negative_stock"),
        CheckConstraint("price >= 0", name="non_negative_price"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    category_code: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("categories.code", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    cover: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    @property
    def category(self) -> str:
        return self.category_code
