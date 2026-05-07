from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.app.core.error_handler import exception_handler
from src.app.core.limiter import limiter
from src.app.core.middlewares import request_logging_middleware
from src.app.core.responses import common_responses
from src.app.core.settings import settings
from src.app.routers import (
    auth,
    board,
    board_comments,
    messages,
    participants,
    pomodoro,
    projects,
    rooms,
    tags,
    user_roles,
    users,
)
from src.app.sockets.server import create_socket_app

fastapi_app = FastAPI(
    title='Group Sessions Platform API',
    version='1.1.0',
)
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.common.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=settings.common.cors_allowed_methods,
    allow_headers=settings.common.cors_allowed_headers,
)

fastapi_app.state.limiter = limiter
fastapi_app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)
fastapi_app.add_middleware(SlowAPIMiddleware)

fastapi_app.add_exception_handler(
    exc_class_or_status_code=Exception,
    handler=exception_handler,
)

api_router = APIRouter(
    prefix='/api/v1',
    responses=common_responses,
)

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(tags.router)
api_router.include_router(rooms.router)
api_router.include_router(participants.router)
api_router.include_router(messages.router)
api_router.include_router(board.router)
api_router.include_router(board_comments.router)
api_router.include_router(pomodoro.router)
api_router.include_router(user_roles.router)

fastapi_app.include_router(api_router)
fastapi_app.middleware('http')(request_logging_middleware)


def custom_openapi():
    if fastapi_app.openapi_schema:
        return fastapi_app.openapi_schema

    openapi_schema = get_openapi(
        title='Group Sessions Platform API',
        version='1.1.0',
        description='API for group study sessions platform',
        routes=fastapi_app.routes,
        servers=[
            {
                'url': settings.common.host,
                'description': 'Local server',
            },
        ],
    )

    fastapi_app.openapi_schema = openapi_schema
    return fastapi_app.openapi_schema


fastapi_app.openapi = custom_openapi


@fastapi_app.get('/health')
async def healthcheck():
    return {'status': 'ok'}


app = create_socket_app(fastapi_app)
