from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_customer(db: Session, user_data: RegisterRequest) -> User:
    user = User(
        name=user_data.name.strip(),
        email=str(user_data.email).lower(),
        hashed_password=hash_password(user_data.password),
        role="customer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
