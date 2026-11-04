from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ai_providers import mask_key
from app.core.security import encrypt_secret
from app.models.ai_key import AIKey
from app.schemas.ai_key import AIKeyCreate


def list_keys(db: Session, user_id: int) -> list[AIKey]:
    return list(
        db.scalars(
            select(AIKey)
            .where(AIKey.user_id == user_id)
            .order_by(AIKey.created_at.desc(), AIKey.id.desc())
        ).all()
    )


def get_key(db: Session, user_id: int, key_id: int) -> AIKey | None:
    return db.scalar(
        select(AIKey).where(AIKey.id == key_id, AIKey.user_id == user_id)
    )


def create_key(db: Session, user_id: int, data: AIKeyCreate) -> AIKey:
    key = AIKey(
        user_id=user_id,
        provider=data.provider,
        label=data.label,
        key_hint=mask_key(data.api_key),
        encrypted_key=encrypt_secret(data.api_key),
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return key


def delete_key(db: Session, key: AIKey) -> None:
    db.delete(key)
    db.commit()
