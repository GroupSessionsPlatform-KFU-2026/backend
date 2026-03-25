from typing import Optional
from uuid import UUID

from fastapi import APIRouter

from src.app.dependencies.services import UserServiceDep
from src.app.models.user import UserPublic

router = APIRouter(
    prefix='/users',
    tags=['users'],
)

# TODO:user/me because we dont have auth


@router.get('/{user_id}')
async def get_user(
    user_service: UserServiceDep,
    user_id: UUID,
) -> Optional[UserPublic]:
    return await user_service.get_user(user_id)
