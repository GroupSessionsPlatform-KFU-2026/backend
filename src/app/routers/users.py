from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.app.dependencies.security import CurrentUserDep
from src.app.dependencies.services import UserServiceDep
from src.app.models.user import UserPublic

router = APIRouter(
    prefix='/users',
    tags=['users'],
)


@router.get('/me')
async def get_me(
    current_user: CurrentUserDep,
) -> UserPublic:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authentication credentials were not provided or are invalid',
        )
    return current_user


@router.get('/{user_id}')
async def get_user(
    user_id: UUID,
    user_service: UserServiceDep,
    current_user: CurrentUserDep,
) -> Optional[UserPublic]:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authentication credentials were not provided or are invalid',
        )

    return await user_service.get_user(user_id)
