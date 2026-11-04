from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

OrderStatus = Literal["pending", "paid", "shipped", "completed", "cancelled"]


class OrderItemCreate(BaseModel):
    book_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=20)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1, max_length=50)


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: int
    title: str
    quantity: int
    unit_price: float


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatus
    total: float
    created_at: datetime
    items: list[OrderItemRead]


class AdminOrderRead(OrderRead):
    user_id: int
    customer_name: str
    customer_email: str
    item_count: int


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
