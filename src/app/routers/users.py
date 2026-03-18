from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Security

from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import UserServiceDep
from src.app.models.user import User as UserModel
from src.app.models.user import UserPublic
from src.app.core.responses import auth_responses, detail_responses
from src.app.utils.errors import NotFoundError

router = APIRouter(
    prefix='/users',
    tags=['users'],
)


@router.get('/me', responses=auth_responses,)
async def get_me(
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['profile:read']),
    ],
) -> UserPublic:
    return current_user


@router.get(
    '/{user_id}',
    dependencies=[Security(require_scoped_user, scopes=['users:read'])],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def get_user(
    user_id: UUID,
    user_service: UserServiceDep,
) -> UserPublic:
    user = await user_service.get_user(user_id)

    if user is None:
        raise NotFoundError

    return user
