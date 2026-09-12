from uuid import uuid4

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from medinote.schemas import ApiError, ErrorDetail


class ServiceError(Exception):
    def __init__(self, code, message, status=503, retry_after_seconds=None):
        self.code = code
        self.message = message
        self.status = status
        self.retry_after_seconds = retry_after_seconds
        super().__init__(code)


def error_response(error, request_id=None):
    body = ApiError(
        error=ErrorDetail(
            code=error.code, message=error.message, retry_after_seconds=error.retry_after_seconds
        ),
        request_id=request_id or uuid4().hex,
    )
    headers = {"Cache-Control": "no-store"}
    if error.retry_after_seconds is not None:
        headers["Retry-After"] = str(error.retry_after_seconds)
    return JSONResponse(body.model_dump(), status_code=error.status, headers=headers)


def register_error_handlers(app):
    @app.exception_handler(ServiceError)
    async def service_error(request, exc):
        return error_response(exc, getattr(request.state, "request_id", None))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return error_response(
            ServiceError("INVALID_REQUEST", "Requête invalide.", 422),
            getattr(request.state, "request_id", None),
        )

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error_response(
            ServiceError(
                "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR",
                "Ressource introuvable." if exc.status_code == 404 else "Requête refusée.",
                exc.status_code,
            ),
            getattr(request.state, "request_id", None),
        )

    @app.exception_handler(Exception)
    async def internal_error(request, exc):
        return error_response(
            ServiceError("INTERNAL_ERROR", "Service temporairement indisponible.", 500),
            getattr(request.state, "request_id", None),
        )
