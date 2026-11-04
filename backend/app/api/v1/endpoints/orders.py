from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DatabaseSession, get_current_user
from app.crud import order as crud
from app.models.order import Order
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DatabaseSession,
) -> Order:
    try:
        return crud.create_order(db, current_user.id, payload)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.get("", response_model=list[OrderRead])
def list_my_orders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: DatabaseSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=50)] = 50,
) -> list[Order]:
    orders, _ = crud.list_orders(
        db, user_id=current_user.id, status=None, skip=skip, limit=limit
    )
    return orders


@router.get("/{order_id}", response_model=OrderRead)
def read_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DatabaseSession,
) -> Order:
    order = crud.get_order(db, order_id)
    if order is None or (
        order.user_id != current_user.id and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    return order
