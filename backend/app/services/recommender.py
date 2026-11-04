import re
from collections import Counter
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.order import Order, OrderItem
from app.models.user import User

CATEGORY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("science-fiction", ("sci-fi", "science fiction", "space", "alien", "future", "dystopian", "robot")),
    ("mystery", ("mystery", "thriller", "detective", "crime", "whodunit", "suspense", "murder")),
    ("fantasy", ("fantasy", "magic", "dragon", "epic", "quest", "wizard")),
    ("romance", ("romance", "romantic", "love story")),
    ("fiction", ("fiction", "literary", "classic", "historical", "drama")),
)

CATEGORY_LABELS = {
    "science-fiction": "science fiction",
    "mystery": "mystery",
    "fantasy": "fantasy",
    "romance": "romance",
    "fiction": "fiction",
}

DEFAULT_SUGGESTIONS = [
    "A cozy mystery",
    "Science fiction under $20",
    "A romance to get lost in",
    "Staff picks",
]

PRICE_RE = re.compile(
    r"(?:under|below|less than|budget of|max(?:imum)?)\s*\$?\s*(\d+(?:\.\d+)?)"
)
DOLLAR_RE = re.compile(r"\$(\d+(?:\.\d+)?)")


def book_popularity(db: Session) -> dict[int, int]:
    rows = db.execute(
        select(OrderItem.book_id, func.sum(OrderItem.quantity))
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.status != "cancelled")
        .group_by(OrderItem.book_id)
    ).all()
    return {book_id: int(total or 0) for book_id, total in rows}


def _rank(books: list[Book], popularity: dict[int, int]) -> list[Book]:
    return sorted(
        books,
        key=lambda book: (
            -popularity.get(book.id, 0),
            -book.stock,
            Decimal(book.price),
            book.id,
        ),
    )


def _available_books(db: Session, category: str | None = None) -> list[Book]:
    stmt = select(Book).where(Book.stock > 0)
    if category:
        stmt = stmt.where(Book.category_code == category)
    return list(db.scalars(stmt).all())


def build_recommendations(
    db: Session, user: User | None, limit: int = 4
) -> tuple[list[Book], str]:
    popularity = book_popularity(db)
    purchased: set[int] = set()
    category_counts: Counter[str] = Counter()

    if user is not None:
        rows = db.execute(
            select(OrderItem.book_id, Book.category_code)
            .join(Order, Order.id == OrderItem.order_id)
            .join(Book, Book.id == OrderItem.book_id)
            .where(Order.user_id == user.id, Order.status != "cancelled")
        ).all()
        for book_id, category_code in rows:
            purchased.add(book_id)
            category_counts[category_code] += 1

    candidates = _available_books(db)
    fresh = [book for book in candidates if book.id not in purchased]
    if len(fresh) >= limit:
        candidates = fresh

    reason = "Reader favourites across the store"
    picked: list[Book] = []

    if category_counts:
        top_category = category_counts.most_common(1)[0][0]
        label = CATEGORY_LABELS.get(top_category, top_category)
        preferred = [book for book in candidates if book.category_code == top_category]
        picked = _rank(preferred, popularity)[:limit]
        reason = f"Because you have been reading {label}"

    if len(picked) < limit:
        remaining = [book for book in _rank(candidates, popularity) if book not in picked]
        picked.extend(remaining[: limit - len(picked)])

    if not picked:
        picked = _rank(_available_books(db), popularity)[:limit]

    return picked, reason


def _detect_category(text: str) -> str | None:
    for category, keywords in CATEGORY_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return category
    return None


def _detect_price(text: str) -> Decimal | None:
    match = PRICE_RE.search(text) or DOLLAR_RE.search(text)
    if not match:
        return None
    value = Decimal(match.group(1))
    if value <= 0 or value > 500:
        return None
    return value


def _suggestions_for(category: str | None) -> list[str]:
    if category is None:
        return list(DEFAULT_SUGGESTIONS)
    label = CATEGORY_LABELS.get(category, category)
    return [f"More {label}", "Keep it under $20", "Something from another genre"]


def answer_chat(
    db: Session, message: str, user: User | None
) -> tuple[str, list[str], list[Book]]:
    text = " ".join(message.casefold().split())
    category = _detect_category(text)
    max_price = _detect_price(text)
    popularity = book_popularity(db)

    if any(word in text for word in ("thank", "thanks", "cheers")):
        return (
            "Anytime! Come back whenever you want another recommendation.",
            _suggestions_for(category),
            [],
        )

    if text in {"hi", "hello", "hey", "good morning", "good evening"}:
        books = _rank(_available_books(db), popularity)[:3]
        return (
            "Hello! I can help you find your next read. Tell me a genre, a mood, "
            "or a budget — for example, “a modern mystery under $20”.",
            list(DEFAULT_SUGGESTIONS),
            books,
        )

    if "what can you do" in text or text == "help":
        return (
            "I am a small local bookseller AI: I know the catalog, the stock levels and "
            "what other readers buy. Ask for a genre, a budget, or a vibe and I will "
            "pull three titles from the shelves.",
            list(DEFAULT_SUGGESTIONS),
            [],
        )

    candidates = _available_books(db, category)
    if max_price is not None:
        candidates = [book for book in candidates if Decimal(book.price) <= max_price]

    label = CATEGORY_LABELS.get(category or "", "all genres")
    if max_price is not None:
        budget = f" under ${max_price:.0f}"
    else:
        budget = ""

    if not candidates:
        fallback = _rank(_available_books(db), popularity)[:3]
        if category or max_price is not None:
            reply = (
                f"I could not find anything in {label}{budget} right now. "
                "Try widening the budget or asking for a different shelf."
            )
        else:
            reply = "I could not find a match for that. Try a genre or a budget."
        return reply, _suggestions_for(category), fallback

    books = _rank(candidates, popularity)[:3]
    if category is not None:
        reply = (
            f"{label.capitalize()} it is. Here are three titles{budget} that readers "
            "keep coming back for. Want something lighter, darker, or longer?"
        )
    elif max_price is not None:
        reply = (
            f"Here are three good reads{budget}. Tell me a genre if you want me to "
            "narrow the shelf."
        )
    else:
        reply = (
            "Here are three books our readers are talking about right now. "
            "Tell me a genre or a budget and I will narrow it down."
        )

    return reply, _suggestions_for(category), books
