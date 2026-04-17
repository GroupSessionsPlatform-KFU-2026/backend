from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.app.dependencies.repositories import (
    RoleRepositoryDep,
    UserRepositoryDep,
    UserRoleRepositoryDep,
)
from src.app.dependencies.security import CurrentUserUsersWriteDep
from src.app.models.user_role import UserRoleLink

router = APIRouter(
    prefix='/users',
    tags=['user-roles'],
)


@router.post('/{user_id}/roles/{role_name}')
async def assign_role_to_user(
    user_id: UUID,
    role_name: str,
    user_repository: UserRepositoryDep,
    role_repository: RoleRepositoryDep,
    user_role_repository: UserRoleRepositoryDep,
    _current_user: CurrentUserUsersWriteDep,
):
    user = await user_repository.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found',
        )

    role = await role_repository.get_one_by_filters(
        extra_filters={'name': role_name},
    )
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Role not found',
        )

    existing_link = await user_role_repository.get_one_by_filters(
        extra_filters={
            'user_id': user_id,
            'role_id': role.id,
        },
    )
    if existing_link is not None:
        return {'success': True, 'detail': 'Role already assigned'}

    await user_role_repository.save(
        UserRoleLink(user_id=user_id, role_id=role.id),
    )

    return {'success': True}