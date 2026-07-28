"""Centralized exception handlers for FastAPI."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DatabaseError(Exception):
    def __init__(self, detail: str = "Database connection failed"):
        self.detail = detail


class ETLRunError(Exception):
    def __init__(self, detail: str = "ETL pipeline failed"):
        self.detail = detail


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        return JSONResponse(status_code=503, content={"error": exc.detail, "type": "database"})

    @app.exception_handler(ETLRunError)
    async def etl_error_handler(request: Request, exc: ETLRunError):
        return JSONResponse(status_code=500, content={"error": exc.detail, "type": "etl"})

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "type": "unknown", "detail": str(exc)},
        )
