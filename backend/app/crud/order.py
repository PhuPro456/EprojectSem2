from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"paid", "cancelled"},
    "paid": {"shipped", "cancelled"},
    "shipped": {"completed"},
    "completed": set(),
    "cancelled": set(),
}


def create_order(db: Session, user_id: int, data: OrderCreate) -> Order:
    quantities: dict[int, int] = {}
    for item in data.items:
        quantities[item.book_id] = quantities.get(item.book_id, 0) + item.quantity

    books = {
        book.id: book
        for book in db.scalars(
            select(Book).where(Book.id.in_(quantities)).with_for_update()
        ).all()
    }
    missing = sorted(set(quantities) - set(books))
    if missing:
        raise LookupError(f"Unknown book ids: {missing}")
    for book_id, quantity in quantities.items():
        if books[book_id].stock < quantity:
            raise ValueError(f"Not enough stock for '{books[book_id].title}'")

    order = Order(user_id=user_id, status="pending", total=Decimal("0"))
    db.add(order)
    db.flush()

    total = Decimal("0")
    for book_id, quantity in quantities.items():
        book = books[book_id]
        total += book.price * quantity
        book.stock -= quantity
        db.add(
            OrderItem(
                order_id=order.id,
                book_id=book.id,
                title=book.title,
                quantity=quantity,
                unit_price=book.price,
            )
        )

    order.total = total
    db.commit()
    db.refresh(order)
    return order


def build_orders_query(*, user_id: int | None = None, status: str | None = None) -> Select:
    stmt = select(Order)
    if user_id is not None:
        stmt = stmt.where(Order.user_id == user_id)
    if status:
        stmt = stmt.where(Order.status == status)
    return stmt.order_by(Order.created_at.desc(), Order.id.desc())


def build_orders_count_query(stmt: Select) -> Select:
    return select(func.count()).select_from(stmt.order_by(None).subquery())


def list_orders(
    db: Session,
    *,
    user_id: int | None,
    status: str | None,
    skip: int,
    limit: int,
) -> tuple[list[Order], int]:
    stmt = build_orders_query(user_id=user_id, status=status)
    total = db.scalar(build_orders_count_query(stmt)) or 0
    orders = list(db.scalars(stmt.offset(skip).limit(limit)).all())
    return orders, total


def get_order(db: Session, order_id: int) -> Order | None:
    return db.get(Order, order_id)


def update_order_status(db: Session, order: Order, new_status: str) -> Order:
    if new_status == order.status:
        return order
    if new_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
        raise ValueError(f"Cannot change order from '{order.status}' to '{new_status}'")

    if new_status == "cancelled":
        for item in order.items:
            book = db.get(Book, item.book_id)
            if book is not None:
                book.stock += item.quantity

    order.status = new_status
    db.commit()
    db.refresh(order)
    return order
