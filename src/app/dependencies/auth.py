from typing import Annotated

from fastapi import Depends, HTTPException

from src.app.dependencies.security import get_current_user
from src.app.models.user import User

CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_scopes(required_scopes: list[str]):
    async def checker(user: CurrentUserDep):
        user_scopes = set()

        for role in user.roles:
            for perm in role.permissions:
                user_scopes.add(perm.scope)

        if not set(required_scopes).issubset(user_scopes):
            raise HTTPException(
                status_code=403,
                detail='Not enough permissions',
            )

        return user

    return checker
