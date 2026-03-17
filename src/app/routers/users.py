from typing import Optional

from fastapi import APIRouter

from src.app.dependencies.services import UserServiceDep
from src.app.models.user import UserPublic

router = APIRouter(
    prefix='/users',
    tags=['users'],
)


@router.get('/me')
async def get_me(user_service: UserServiceDep) -> Optional[UserPublic]:
    # temporal: luego reemplazas por current_user real desde auth
    return await user_service.get_me(1)


@router.get('/{user_id}')
async def get_user(
    user_service: UserServiceDep,
    user_id: int,
) -> Optional[UserPublic]:
    return await user_service.get_user(user_id)
