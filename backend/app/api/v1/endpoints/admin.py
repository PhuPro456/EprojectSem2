from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import DatabaseSession, get_current_admin
from app.models.user import User
from app.schemas.auth import RoleUpdateRequest, UserRead

router = APIRouter(
    prefix="/admin",
    tags=["administration"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/users", response_model=list[UserRead])
def list_users(db: DatabaseSession) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)).all())


@router.patch("/users/{user_id}/role", response_model=UserRead)
def update_user_role(
    user_id: int,
    role_update: RoleUpdateRequest,
    db: DatabaseSession,
    current_admin: Annotated[User, Depends(get_current_admin)],
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == current_admin.id and role_update.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot remove your own administrator role",
        )

    if user.role == "admin" and role_update.role != "admin":
        admin_count = db.scalar(
            select(func.count()).select_from(User).where(User.role == "admin")
        )
        if admin_count == 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The last administrator cannot be demoted",
            )

    user.role = role_update.role
    db.commit()
    db.refresh(user)
    return user
