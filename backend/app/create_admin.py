from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db.init_db import initialize_database
from app.db.session import SessionLocal
from app.models.user import User


def main() -> None:
    try:
        email = str(TypeAdapter(EmailStr).validate_python(input("Admin email: "))).lower()
    except ValidationError as exc:
        raise SystemExit("Please enter a valid email address.") from exc

    password = getpass("Admin password (at least 8 characters): ")
    confirmation = getpass("Confirm admin password: ")
    if len(password) < 8:
        raise SystemExit("Password must contain at least 8 characters.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    initialize_database()
    with SessionLocal() as db:
        if db.query(User).filter(User.email == email).first() is not None:
            raise SystemExit("An account with this email already exists.")

        db.add(
            User(
                name="Administrator",
                email=email,
                hashed_password=hash_password(password),
                role="admin",
            )
        )
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise SystemExit("Could not create administrator; the email may already exist.") from exc

    print(f"Administrator account created for {email}.")


if __name__ == "__main__":
    main()
