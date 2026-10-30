from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.v1.api import api_router
from app.db.init_db import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


app = FastAPI(
    title="BookStore API",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}