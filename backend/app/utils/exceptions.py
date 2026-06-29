from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.utils.responses import error_response


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):  # noqa: ARG001
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                message=detail,
                code=f"HTTP_{exc.status_code}",
                details=exc.detail,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):  # noqa: ARG001
        return JSONResponse(
            status_code=422,
            content=error_response(
                message="Validation error",
                code="VALIDATION_ERROR",
                details=exc.errors(),
            ),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):  # noqa: ARG001
        return JSONResponse(
            status_code=500,
            content=error_response(
                message="Internal server error",
                code="INTERNAL_SERVER_ERROR",
            ),
        )

