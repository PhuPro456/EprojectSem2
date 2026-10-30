import os
from collections.abc import Generator

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-only-secret-key-with-at-least-32-characters"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine, get_db
from app.main import app
from app.models.user import User


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        with SessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def register_customer(client: TestClient, email: str = "reader@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Book Reader",
            "email": email,
            "password": "secure-password",
        },
    )
    assert response.status_code == 201
    return response.json()


def login(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "secure-password"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_register_login_and_read_profile(client: TestClient) -> None:
    registered = register_customer(client)
    assert registered["role"] == "customer"
    assert "hashed_password" not in registered

    token = login(client, "reader@example.com")
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "reader@example.com"


def test_registration_cannot_assign_admin_role(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Reader",
            "email": "reader@example.com",
            "password": "secure-password",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "customer"

    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Another Reader",
            "email": "READER@example.com",
            "password": "secure-password",
        },
    )
    assert duplicate.status_code == 409


def test_registration_rejects_blank_names(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "   ",
            "email": "reader@example.com",
            "password": "secure-password",
        },
    )
    assert response.status_code == 422


def test_invalid_login_and_missing_token_are_rejected(client: TestClient) -> None:
    register_customer(client)
    bad_login = client.post(
        "/api/v1/auth/login",
        data={"username": "reader@example.com", "password": "incorrect"},
    )
    assert bad_login.status_code == 401

    no_token = client.get("/api/v1/auth/me")
    assert no_token.status_code == 401


def test_customer_cannot_manage_roles(client: TestClient) -> None:
    register_customer(client)
    token = login(client, "reader@example.com")
    response = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_admin_can_change_role_but_not_demote_self(client: TestClient) -> None:
    register_customer(client)
    with SessionLocal() as db:
        admin = User(
            name="Administrator",
            email="admin@example.com",
            hashed_password=hash_password("secure-password"),
            role="admin",
        )
        db.add(admin)
        db.commit()
        admin_id = admin.id

    token = login(client, "admin@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    changed = client.patch(
        "/api/v1/admin/users/1/role",
        json={"role": "admin"},
        headers=headers,
    )
    assert changed.status_code == 200
    assert changed.json()["role"] == "admin"

    self_demotion = client.patch(
        f"/api/v1/admin/users/{admin_id}/role",
        json={"role": "customer"},
        headers=headers,
    )
    assert self_demotion.status_code == 409
