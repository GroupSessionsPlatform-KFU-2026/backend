from fastapi import Request

from src.app.core.error_handler import exception_handler
from src.app.utils.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from src.app.utils.logger import logger

EXPECTED_ERROR_STATUS_CODES = {
    UnauthorizedError: 401,
    ForbiddenError: 403,
    NotFoundError: 404,
    ConflictError: 409,
}


async def request_logging_middleware(request: Request, call_next):
    logger.info(
        'Request started',
        extra={
            'path': request.url.path,
            'method': request.method,
            'client_host': request.client.host if request.client else None,
        },
    )

    try:
        response = await call_next(request)
    except Exception as exc:
        for error_cls, status_code in EXPECTED_ERROR_STATUS_CODES.items():
            if isinstance(exc, error_cls):
                response = await exception_handler(request, exc)
                logger.info(
                    'Request finished',
                    extra={
                        'path': request.url.path,
                        'method': request.method,
                        'status_code': status_code,
                    },
                )
                return response

        logger.error(
            'Unhandled exception encountered',
            extra={
                'path': request.url.path,
                'method': request.method,
                'client_host': request.client.host if request.client else None,
            },
            exc_info=True,
        )
        raise

    logger.info(
        'Request finished',
        extra={
            'path': request.url.path,
            'method': request.method,
            'status_code': response.status_code,
        },
    )

    return response
