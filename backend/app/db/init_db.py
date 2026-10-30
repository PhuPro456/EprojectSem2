from app.db.session import Base, engine
from app.models.user import User  # noqa: F401


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
