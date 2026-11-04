import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.mock_data import BOOKS
from app.db.session import Base, SessionLocal, engine
from app.models.ai_key import AIKey  # noqa: F401
from app.models.book import Book, Category
from app.models.order import Order, OrderItem
from app.models.review import Review
from app.models.user import User
from app.services.sentiment import analyze_sentiment

DEMO_PASSWORD = "reader-password-1"
DEMO_CUSTOMERS = (
    ("Maya Chen", "maya.chen@example.com", 248),
    ("Daniel Okafor", "daniel.okafor@example.com", 226),
    ("Priya Raman", "priya.raman@example.com", 193),
    ("Lucas Meyer", "lucas.meyer@example.com", 157),
    ("Sofia Rossi", "sofia.rossi@example.com", 84),
)

DEMO_REVIEWS = (
    ("Absolutely loved it — vivid characters and a gripping plot.", 5),
    ("A beautiful, moving story that stayed with me for days.", 5),
    ("Clever and fast-paced, a proper page-turner.", 4),
    ("The prose is gorgeous but the plot felt messy and shallow.", 3),
    ("Boring and predictable. I kept waiting for something to happen.", 2),
    ("A cozy, heartwarming read — perfect for a rainy weekend.", 5),
    ("Confusing timeline and a weak ending.", 2),
    ("Thrilling, immersive and beautifully written.", 5),
    ("Not for me — dull characters and a tedious middle section.", 1),
    ("Really enjoyed this one, would recommend to any mystery fan.", 5),
    ("Solid story, though the middle dragged a little.", 3),
    ("An outstanding novel with memorable characters.", 5),
    ("The world-building is amazing; the pacing is perfect.", 5),
    ("I wanted to love it, but it was repetitive and bland.", 2),
    ("A refreshing, thoughtful take on a classic idea.", 4),
    ("Disappointing — the twist was predictable.", 2),
    ("Charming and fun, exactly what I needed.", 5),
    ("Beautifully written, with a satisfying ending.", 5),
)


def _category_code(name: str) -> str:
    return "-".join(name.casefold().split())


def seed_books(db: Session) -> None:
    if db.scalar(select(Book.id).limit(1)) is not None:
        return

    categories = {
        _category_code(book["category"]): book["category"] for book in BOOKS
    }
    db.add_all(
        Category(code=code, name=name) for code, name in categories.items()
    )
    db.flush()

    db.add_all(
        Book(
            title=book["title"],
            author=book["author"],
            category_code=_category_code(book["category"]),
            description=book["description"],
            price=Decimal(str(book["price"])),
            stock=book["stock"],
            cover=book["cover"],
        )
        for book in BOOKS
    )
    db.commit()


def _is_ephemeral_database() -> bool:
    """Skip demo customers/orders/reviews for in-memory test databases."""
    return engine.url.get_backend_name() == "sqlite" and not engine.url.database


def seed_admin(db: Session) -> None:
    """Create the demo administrator so the admin console is reachable."""
    settings = get_settings()
    if not settings.seed_admin:
        return
    if db.scalar(select(User.id).where(User.role == "admin")) is not None:
        return

    db.add(
        User(
            name=settings.admin_name,
            email=settings.admin_email,
            hashed_password=hash_password(settings.admin_password),
            role="admin",
        )
    )
    db.commit()


def seed_demo_data(db: Session) -> None:
    if db.scalar(
        select(User.id).where(
            User.email.in_([email for _, email, _ in DEMO_CUSTOMERS])
        )
    ):
        return

    now = datetime.now(timezone.utc)
    password_hash = hash_password(DEMO_PASSWORD)
    customers = [
        User(
            name=name,
            email=email,
            hashed_password=password_hash,
            role="customer",
            created_at=now - timedelta(days=signup_days, hours=signup_days % 9 + 8),
        )
        for name, email, signup_days in DEMO_CUSTOMERS
    ]
    db.add_all(customers)
    db.commit()
    for customer in customers:
        db.refresh(customer)

    books = list(db.scalars(select(Book).order_by(Book.id)).all())
    if not books:
        return

    rng = random.Random(20261030)
    statuses = ["completed", "completed", "completed", "shipped", "paid", "pending", "cancelled"]
    signup_days = {email: days for _, email, days in DEMO_CUSTOMERS}

    # Historical orders: stock counts in the catalog are already the "current"
    # levels, so seeding does not decrement inventory.
    for _ in range(34):
        customer = rng.choice(customers)
        window = max(1, min(225, signup_days[customer.email] - 3))
        created = now - timedelta(
            days=rng.randint(0, window), hours=rng.randint(8, 20)
        )
        order = Order(
            user_id=customer.id,
            status=rng.choice(statuses),
            total=Decimal("0"),
            created_at=created,
        )
        db.add(order)
        db.flush()

        total = Decimal("0")
        for book in rng.sample(books, k=rng.randint(1, 3)):
            quantity = rng.randint(1, 2)
            total += book.price * quantity
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
    seed_demo_reviews(db, customers, books, rng)


def seed_demo_reviews(
    db: Session,
    customers: list[User],
    books: list[Book],
    rng: random.Random,
) -> None:
    if db.scalar(select(Review.id).limit(1)) is not None:
        return

    now = datetime.now(timezone.utc)
    for index, (text, rating) in enumerate(DEMO_REVIEWS):
        sentiment, keywords = analyze_sentiment(text, rating)
        db.add(
            Review(
                book_id=books[index % len(books)].id,
                user_id=customers[index % len(customers)].id,
                author_name=customers[index % len(customers)].name,
                rating=rating,
                text=text,
                sentiment=sentiment,
                keywords=keywords,
                created_at=now - timedelta(days=rng.randint(0, 120)),
            )
        )
    db.commit()


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_books(db)
        if not _is_ephemeral_database():
            seed_admin(db)
            seed_demo_data(db)
