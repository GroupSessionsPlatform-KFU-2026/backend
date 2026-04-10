from typing import Optional
from uuid import UUID

from fastapi import APIRouter

from src.app.dependencies.security import CurrentProfileUserDep, CurrentUsersReadUserDep
from src.app.dependencies.services import UserServiceDep
from src.app.models.user import UserPublic

router = APIRouter(
    prefix='/users',
    tags=['users'],
)


@router.get('/me')
async def get_me(
    current_user: CurrentProfileUserDep,
) -> UserPublic:
    return current_user


@router.get('/{user_id}')
async def get_user(
    user_id: UUID,
    user_service: UserServiceDep,
    _current_user: CurrentUsersReadUserDep,
) -> Optional[UserPublic]:
    return await user_service.get_user(user_id)
