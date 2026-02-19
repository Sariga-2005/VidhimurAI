"""Global error handlers for the FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def register_error_handlers(app: FastAPI) -> None:
    """Attach custom exception handlers to the app instance."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "Request body validation failed.",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(
        _request: Request,
        exc: FileNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": "dataset_unavailable",
                "message": str(exc),
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": f"An unexpected error occurred: {exc}",
            },
        )
