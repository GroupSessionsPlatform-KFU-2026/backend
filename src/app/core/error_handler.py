from fastapi import Request
from fastapi.responses import JSONResponse

from src.app.core.responses import (
    auth_responses,
    common_responses,
    conflict_responses,
    detail_responses,
)
from src.app.schemas.errors import ErrorSchema, InternalServerErrorSchema


async def exception_handler(_: Request, exc: Exception):
    status_code = 500
    response_schema: ErrorSchema = InternalServerErrorSchema()

    expected_responses = {
        **common_responses,
        **auth_responses,
        **detail_responses,
        **conflict_responses,
    }

    for code, config in expected_responses.items():
        model = config.get('model', InternalServerErrorSchema)
        schema = model()

        if isinstance(exc, schema.error_cls):
            status_code = code
            response_schema = schema
            break

    return JSONResponse(
        status_code=status_code,
        content={
            'message': getattr(exc, 'message', response_schema.message),
            'detail': getattr(exc, 'detail', None),
        },
    )