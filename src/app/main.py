from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from sqlmodel.ext.asyncio.session import AsyncSession

from src.app.db.engine import engine
from src.app.models.permission import Permission
from src.app.models.role import Role
from src.app.models.role_permission import RolePermissionLink
from src.app.models.user import User
from src.app.models.user_role import UserRoleLink
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
from src.app.services.rbac_bootstrap import RBACBootstrapService
from src.app.sockets.server import create_socket_app
from src.app.utils.repository import Repository


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with AsyncSession(engine) as session:
        bootstrap_service = RBACBootstrapService(
            permission_repository=Repository[Permission](session),
            role_repository=Repository[Role](session),
            role_permission_repository=Repository[RolePermissionLink](session),
            user_repository=Repository[User](session),
            user_role_repository=Repository[UserRoleLink](session),
        )
        await bootstrap_service.bootstrap()
    yield


fastapi_app = FastAPI(
    title='Group Sessions Platform API',
    version='1.1.0',
    lifespan=lifespan,
)

api_router = APIRouter(prefix='/api/v1')
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


@fastapi_app.get('/health')
async def healthcheck():
    return {'status': 'ok'}


app = create_socket_app(fastapi_app)
