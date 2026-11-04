from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review import Review
from app.models.user import User
from app.schemas.review import KeywordCount, ReviewCreate, ReviewSummary
from app.services.sentiment import analyze_sentiment


def list_reviews(db: Session, book_id: int, limit: int = 50) -> list[Review]:
    return list(
        db.scalars(
            select(Review)
            .where(Review.book_id == book_id)
            .order_by(Review.created_at.desc(), Review.id.desc())
            .limit(limit)
        ).all()
    )


def all_reviews(db: Session) -> list[Review]:
    return list(
        db.scalars(
            select(Review).order_by(Review.created_at.desc(), Review.id.desc())
        ).all()
    )


def recent_reviews(db: Session, limit: int = 40) -> list[Review]:
    return list(
        db.scalars(
            select(Review)
            .order_by(Review.created_at.desc(), Review.id.desc())
            .limit(limit)
        ).all()
    )


def build_summary(reviews: list[Review]) -> ReviewSummary:
    counts = Counter(review.sentiment for review in reviews)
    average = (
        round(sum(review.rating for review in reviews) / len(reviews), 2)
        if reviews
        else 0.0
    )
    return ReviewSummary(
        total=len(reviews),
        positive=counts.get("positive", 0),
        neutral=counts.get("neutral", 0),
        negative=counts.get("negative", 0),
        average_rating=average,
    )


def create_review(
    db: Session, book_id: int, user: User, data: ReviewCreate
) -> Review:
    sentiment, keywords = analyze_sentiment(data.text, data.rating)
    review = Review(
        book_id=book_id,
        user_id=user.id,
        author_name=user.name,
        rating=data.rating,
        text=data.text,
        sentiment=sentiment,
        keywords=keywords,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def keyword_counts(reviews: list[Review], sentiment: str, limit: int = 6) -> list[KeywordCount]:
    counter: Counter[str] = Counter()
    for review in reviews:
        if review.sentiment == sentiment:
            counter.update(review.keywords or [])
    return [
        KeywordCount(keyword=keyword, count=count)
        for keyword, count in counter.most_common(limit)
    ]
