from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.exceptions import (
    AppError,
    ConflictError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    for error_cls, status_code in STATUS_BY_ERROR.items():
        app.add_exception_handler(error_cls, _make_handler(status_code=status_code))

def _make_handler(status_code: int):
    async def handler(_: Request, exc: AppError):
        return JSONResponse(status_code = status_code, content={"detail": exc.message})
    return handler

STATUS_BY_ERROR: dict[type[AppError], int] = {
    ConflictError: 409, 
    ForbiddenError: 403, 
    NotFoundError: 404,
    ExternalServiceError: 502
}