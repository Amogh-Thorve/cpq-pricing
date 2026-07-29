from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Any, Dict, Optional

class APIErrorResponse(BaseModel):
    """
    Standardized API error response format across the entire platform.
    """
    detail: str
    error_code: str
    details: Optional[Dict[str, Any]] = None

class CPQException(Exception):
    """
    Base exception for CPQ domain errors.
    """
    def __init__(
        self, 
        detail: str, 
        error_code: str, 
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.detail = detail
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(detail)

class DomainValidationError(CPQException):
    """
    Raised when business rules or configuration validation fails.
    """
    def __init__(self, detail: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )

class EntityNotFoundError(CPQException):
    """
    Raised when a requested resource is not found in the database.
    """
    def __init__(self, detail: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )

class UnauthorizedError(CPQException):
    """
    Raised when credentials verification fails or permission is denied.
    """
    def __init__(self, detail: str = "Could not validate credentials", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            error_code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )

def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers custom global exception handlers with the FastAPI application.
    """
    @app.exception_handler(CPQException)
    async def cpq_exception_handler(request: Request, exc: CPQException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": exc.error_code,
                "details": exc.details
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Standardize pydantic input validation failures to match APIErrorResponse format
        errors = exc.errors()
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Request body validation failed.",
                "error_code": "REQUEST_VALIDATION_ERROR",
                "details": {"validation_errors": errors}
            }
        )

    @app.exception_handler(Exception)
    async def fallback_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Prevent leaking raw system exception messages to users in production
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected internal server error occurred.",
                "error_code": "INTERNAL_SERVER_ERROR",
                "details": None
            }
        )
