from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import engine, get_db
from core.error_handlers import register_exception_handlers
from routers import auth, notifications, users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with httpx.AsyncClient() as http_client:
        app.state.http_client = http_client
        yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

@app.get("/health")
async def health_check(db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    return {"status": "healthy"}

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    response.headers["X-Content-Type-Options"] = "nosniff"

    if "Referrer-Policy" not in response.headers:
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if request.url.hostname not in ("localhost", "127.0.0.1"):
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )

    return response
