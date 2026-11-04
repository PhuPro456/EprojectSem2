from collections import Counter, defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.order import Order
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverview,
    CategoryPoint,
    CustomerMonthPoint,
    CustomerRow,
    MonthlyPoint,
    ProductPoint,
    StatusPoint,
)

SERIES_MONTHS = 8
LOW_STOCK_THRESHOLD = 10
REVENUE_STATUSES = {"pending", "paid", "shipped", "completed"}


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _month_series(months: int = SERIES_MONTHS) -> list[tuple[int, int]]:
    now = datetime.now(timezone.utc)
    year, month = now.year, now.month
    keys: list[tuple[int, int]] = []
    for _ in range(months):
        keys.append((year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return list(reversed(keys))


def _label(key: tuple[int, int]) -> str:
    return datetime(key[0], key[1], 1).strftime("%b")


def _month_key(value: datetime) -> tuple[int, int]:
    return value.year, value.month


def _round(value: float) -> float:
    return round(value, 2)


def build_overview(db: Session) -> AnalyticsOverview:
    orders = list(db.scalars(select(Order)).all())
    books = list(db.scalars(select(Book)).all())
    users = list(db.scalars(select(User)).all())

    books_by_id = {book.id: book for book in books}
    users_by_id = {user.id: user for user in users}
    series = _month_series()
    series_set = set(series)

    monthly_revenue: dict[tuple[int, int], float] = defaultdict(float)
    monthly_orders: dict[tuple[int, int], int] = defaultdict(int)
    category_revenue: dict[str, float] = defaultdict(float)
    category_units: dict[str, int] = defaultdict(int)
    product_units: dict[int, int] = defaultdict(int)
    product_revenue: dict[int, float] = defaultdict(float)
    product_titles: dict[int, str] = {}
    status_counts = Counter(order.status for order in orders)
    customer_orders: Counter[int] = Counter()
    customer_spend: dict[int, float] = defaultdict(float)

    total_revenue = 0.0
    units_sold = 0
    counted_orders = 0

    for order in orders:
        if order.status not in REVENUE_STATUSES:
            continue
        counted_orders += 1
        amount = float(order.total)
        total_revenue += amount

        created = _aware(order.created_at)
        if created is not None:
            key = _month_key(created)
            if key in series_set:
                monthly_revenue[key] += amount
                monthly_orders[key] += 1

        customer_orders[order.user_id] += 1
        customer_spend[order.user_id] += amount

        for item in order.items:
            quantity = int(item.quantity)
            line_total = float(item.unit_price) * quantity
            units_sold += quantity

            book = books_by_id.get(item.book_id)
            category = book.category_code if book else "unknown"
            category_revenue[category] += line_total
            category_units[category] += quantity

            product_units[item.book_id] += quantity
            product_revenue[item.book_id] += line_total
            product_titles.setdefault(item.book_id, item.title)

    sales_by_month = [
        MonthlyPoint(
            label=_label(key),
            revenue=_round(monthly_revenue[key]),
            orders=monthly_orders[key],
        )
        for key in series
    ]

    growth_rate = 0.0
    if len(sales_by_month) >= 2:
        previous = sales_by_month[-2].revenue
        current = sales_by_month[-1].revenue
        if previous > 0:
            growth_rate = _round((current - previous) / previous * 100)
        elif current > 0:
            growth_rate = 100.0

    sales_by_category = sorted(
        (
            CategoryPoint(
                category=category,
                revenue=_round(revenue),
                units=category_units[category],
            )
            for category, revenue in category_revenue.items()
        ),
        key=lambda point: point.revenue,
        reverse=True,
    )

    top_products = sorted(
        (
            ProductPoint(
                book_id=book_id,
                title=product_titles[book_id],
                units=units,
                revenue=_round(product_revenue[book_id]),
            )
            for book_id, units in product_units.items()
        ),
        key=lambda point: (point.revenue, point.units),
        reverse=True,
    )[:6]

    order_statuses = [
        StatusPoint(status=status, count=status_counts.get(status, 0))
        for status in ("pending", "paid", "shipped", "completed", "cancelled")
    ]

    top_customers = sorted(
        (
            CustomerRow(
                user_id=user_id,
                name=users_by_id[user_id].name if user_id in users_by_id else "Deleted user",
                email=users_by_id[user_id].email if user_id in users_by_id else "",
                orders=count,
                spend=_round(customer_spend[user_id]),
            )
            for user_id, count in customer_orders.items()
        ),
        key=lambda row: (row.spend, row.orders),
        reverse=True,
    )[:6]

    new_customer_counts: dict[tuple[int, int], int] = defaultdict(int)
    for user in users:
        if user.role != "customer":
            continue
        created = _aware(user.created_at)
        if created is not None:
            new_customer_counts[_month_key(created)] += 1

    new_customers_by_month = [
        CustomerMonthPoint(label=_label(key), new_customers=new_customer_counts[key])
        for key in series
    ]

    total_customers = sum(1 for user in users if user.role == "customer")
    repeat_customers = sum(
        1
        for user_id, count in customer_orders.items()
        if count >= 2 and users_by_id.get(user_id, None) is not None
    )
    inventory_value = sum(float(book.price) * book.stock for book in books)
    low_stock_books = sum(1 for book in books if book.stock <= LOW_STOCK_THRESHOLD)
    average_order_value = total_revenue / counted_orders if counted_orders else 0.0

    return AnalyticsOverview(
        total_revenue=_round(total_revenue),
        total_orders=counted_orders,
        units_sold=units_sold,
        average_order_value=_round(average_order_value),
        total_customers=total_customers,
        repeat_customers=repeat_customers,
        low_stock_books=low_stock_books,
        inventory_value=_round(inventory_value),
        growth_rate=growth_rate,
        sales_by_month=sales_by_month,
        sales_by_category=sales_by_category,
        top_products=top_products,
        order_statuses=order_statuses,
        top_customers=top_customers,
        new_customers_by_month=new_customers_by_month,
    )
