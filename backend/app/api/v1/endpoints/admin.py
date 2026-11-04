from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import DatabaseSession, get_current_admin
from app.crud import order as order_crud
from app.crud import review as review_crud
from app.models.order import Order
from app.models.user import User
from app.schemas.auth import RoleUpdateRequest, UserRead
from app.schemas.order import AdminOrderRead, OrderStatus, OrderStatusUpdate
from app.schemas.review import RecentReviewRead, ReviewDashboard, ReviewRead

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


@router.get("/orders", response_model=list[AdminOrderRead])
def list_orders(
    db: DatabaseSession,
    order_status: Annotated[OrderStatus | None, Query(alias="status")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[Order]:
    orders, _ = order_crud.list_orders(
        db,
        user_id=None,
        status=order_status,
        skip=skip,
        limit=limit,
    )
    return orders


@router.patch("/orders/{order_id}/status", response_model=AdminOrderRead)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: DatabaseSession,
) -> Order:
    order = order_crud.get_order(db, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    try:
        return order_crud.update_order_status(db, order, payload.status)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.get("/reviews", response_model=ReviewDashboard)
def reviews_dashboard(
    db: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=200)] = 40,
) -> ReviewDashboard:
    reviews = review_crud.all_reviews(db)
    return ReviewDashboard(
        summary=review_crud.build_summary(reviews),
        positive_keywords=review_crud.keyword_counts(reviews, "positive"),
        negative_keywords=review_crud.keyword_counts(reviews, "negative"),
        items=[
            RecentReviewRead(
                **ReviewRead.model_validate(review).model_dump(),
                book_title=review.book.title if review.book else "Deleted book",
            )
            for review in reviews[:limit]
        ],
    )