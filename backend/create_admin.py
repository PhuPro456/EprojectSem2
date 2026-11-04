"""Create or promote an administrator account for Bookstore Pro.

Usage (from the backend directory, with DATABASE_URL and SECRET_KEY set):

    python create_admin.py --email admin@bookstorepro.com --name "Store Admin"
    python create_admin.py --email admin@bookstorepro.com --promote-only
"""

import argparse
import getpass
import sys

from pydantic import EmailStr, TypeAdapter
from sqlalchemy import select

from app.core.security import hash_password
from app.db.init_db import initialize_database
from app.db.session import SessionLocal
from app.models.user import User

email_adapter = TypeAdapter(EmailStr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or promote an administrator.")
    parser.add_argument("--email", required=True, help="Account email address")
    parser.add_argument("--name", default="Store Admin", help="Display name")
    parser.add_argument(
        "--password",
        help="Password for a new account (prompted securely when omitted)",
    )
    parser.add_argument(
        "--promote-only",
        action="store_true",
        help="Only promote an existing account; never create a new one",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        email = str(email_adapter.validate_python(args.email.strip().lower()))
    except ValueError as exc:
        sys.exit(f"Invalid email address: {exc}")
    initialize_database()

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:
            user.role = "admin"
            if args.password and not args.promote_only:
                user.hashed_password = hash_password(args.password)
            db.commit()
            print(f"Promoted {email} to administrator.")
            return

        if args.promote_only:
            sys.exit(f"No account exists for {email}.")

        password = args.password or getpass.getpass("Password (min 8 characters): ")
        if len(password) < 8:
            sys.exit("Password must be at least 8 characters.")

        db.add(
            User(
                name=args.name.strip() or "Store Admin",
                email=email,
                hashed_password=hash_password(password),
                role="admin",
            )
        )
        db.commit()
        print(f"Created administrator {email}.")


if __name__ == "__main__":
    main()
