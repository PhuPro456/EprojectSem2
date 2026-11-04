from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    ai,
    ai_keys,
    analytics,
    auth,
    books,
    books_async,
    orders,
    reviews,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(books.router)
api_router.include_router(books_async.router)
api_router.include_router(orders.router)
api_router.include_router(reviews.router)
api_router.include_router(ai.router)
api_router.include_router(ai_keys.router)
api_router.include_router(analytics.router)
