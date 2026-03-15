"""
Custom Exceptions and Exception Handlers for Elder AI Guardian
"""

from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import logger


class ElderAIException(Exception):
    """Base exception for all custom exceptions"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class MLModelError(ElderAIException):
    """Exception raised for ML model errors"""
    
    def __init__(
        self,
        model_name: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not message:
            message = f"ML model {model_name} error"
        
        super().__init__(
            message=message,
            status_code=500,
            error_code="ML_MODEL_ERROR",
            details={"model_name": model_name, **(details or {})}
        )


class AuthenticationError(ElderAIException):
    """Authentication related errors"""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )


class AuthorizationError(ElderAIException):
    """Authorization related errors"""
    
    def __init__(
        self,
        message: str = "Not authorized",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details
        )


class ResourceNotFoundError(ElderAIException):
    """Resource not found errors"""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        message: Optional[str] = None
    ):
        if not message:
            message = f"{resource_type} not found"
            if resource_id:
                message += f": {resource_id}"
        
        super().__init__(
            message=message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class ValidationError(ElderAIException):
    """Data validation errors"""
    
    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details
        )


class DatabaseError(ElderAIException):
    """Database related errors"""
    
    def __init__(
        self,
        message: str = "Database error occurred",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details=details
        )


class ExternalServiceError(ElderAIException):
    """External service errors"""
    
    def __init__(
        self,
        service: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if not message:
            message = f"External service {service} error"
        
        super().__init__(
            message=message,
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, **(details or {})}
        )


# ============================================================================
# Exception Handlers
# ============================================================================

async def elder_ai_exception_handler(request: Request, exc: ElderAIException) -> JSONResponse:
    """Handler for ElderAIException"""
    logger.error(f"ElderAIException: {exc.message} (code: {exc.error_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handler for HTTPException"""
    logger.error(f"HTTPException: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for validation errors"""
    logger.error(f"ValidationError: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": exc.errors()
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred"
            }
        }
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup exception handlers for the FastAPI app
    """
    # Register custom exception handlers
    app.add_exception_handler(ElderAIException, elder_ai_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("✅ Exception handlers configured")