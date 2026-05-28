import pytest
from fastapi import Response, status
from src.app.core.error_handler import exception_handler
from src.app.core.middlewares import request_logging_middleware
from src.app.main import fastapi_app
from src.app.utils.errors import ConflictError, NotFoundError
from starlette.requests import Request


def build_request() -> Request:
    return Request(
        {
            'type': 'http',
            'method': 'GET',
            'path': '/test',
            'headers': [],
            'client': ('127.0.0.1', 12345),
            'scheme': 'http',
            'server': ('test', 80),
        }
    )


async def test_exception_handler_maps_known_and_unknown_errors():
    not_found_response = await exception_handler(build_request(), NotFoundError())
    assert not_found_response.status_code == status.HTTP_404_NOT_FOUND

    conflict_response = await exception_handler(build_request(), ConflictError())
    assert conflict_response.status_code == status.HTTP_409_CONFLICT

    unknown_response = await exception_handler(build_request(), RuntimeError('boom'))
    assert unknown_response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


async def test_request_logging_middleware_success_expected_error_and_unhandled_error():
    request = build_request()

    async def success_call_next(_request):
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    success_response = await request_logging_middleware(request, success_call_next)
    assert success_response.status_code == status.HTTP_204_NO_CONTENT

    async def expected_error_call_next(_request):
        raise NotFoundError()

    expected_error_response = await request_logging_middleware(
        request,
        expected_error_call_next,
    )
    assert expected_error_response.status_code == status.HTTP_404_NOT_FOUND

    async def unhandled_error_call_next(_request):
        raise RuntimeError('boom')

    with pytest.raises(RuntimeError, match='boom'):
        await request_logging_middleware(request, unhandled_error_call_next)


def test_custom_openapi_schema_is_cached():
    fastapi_app.openapi_schema = None

    schema = fastapi_app.openapi()
    cached_schema = fastapi_app.openapi()

    assert schema is cached_schema
    assert schema['info']['title'] == 'Group Sessions Platform API'
    assert schema['servers'][0]['description'] == 'Local server'
