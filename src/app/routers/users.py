from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.app.dependencies.security import CurrentUserDep
from src.app.dependencies.services import UserServiceDep
from src.app.models.user import UserPublic

from fastapi import Security
from src.app.dependencies.security import get_current_user
from src.app.models.user import User


router = APIRouter(
    prefix='/users',
    tags=['users'],
)


@router.get('/me')
async def get_me(
    current_user: User = Security(get_current_user, scopes=['users:read']),
) -> UserPublic:
    return current_user


@router.get('/{user_id}')
async def get_user(
    user_id: UUID,
    user_service: UserServiceDep,
    current_user: User = Security(get_current_user, scopes=['users:read']),
) -> Optional[UserPublic]:
    return await user_service.get_user(user_id)