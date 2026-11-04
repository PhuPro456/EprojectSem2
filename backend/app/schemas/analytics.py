from pydantic import BaseModel


class MonthlyPoint(BaseModel):
    label: str
    revenue: float
    orders: int


class CategoryPoint(BaseModel):
    category: str
    revenue: float
    units: int


class ProductPoint(BaseModel):
    book_id: int
    title: str
    units: int
    revenue: float


class StatusPoint(BaseModel):
    status: str
    count: int


class CustomerRow(BaseModel):
    user_id: int
    name: str
    email: str
    orders: int
    spend: float


class CustomerMonthPoint(BaseModel):
    label: str
    new_customers: int


class AnalyticsOverview(BaseModel):
    total_revenue: float
    total_orders: int
    units_sold: int
    average_order_value: float
    total_customers: int
    repeat_customers: int
    low_stock_books: int
    inventory_value: float
    growth_rate: float
    sales_by_month: list[MonthlyPoint]
    sales_by_category: list[CategoryPoint]
    top_products: list[ProductPoint]
    order_statuses: list[StatusPoint]
    top_customers: list[CustomerRow]
    new_customers_by_month: list[CustomerMonthPoint]
