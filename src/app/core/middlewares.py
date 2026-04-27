from fastapi import Request

from src.app.utils.logger import logger


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
        logger.error(
            'Unhandled exception encountered',
            extra={
                'path': request.url.path,
                'method': request.method,
                'client_host': request.client.host if request.client else None,
            },
            exc_info=True,
        )
        raise exc

    logger.info(
        'Request finished',
        extra={
            'path': request.url.path,
            'method': request.method,
            'status_code': response.status_code,
        },
    )

    return response
