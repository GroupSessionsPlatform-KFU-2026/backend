from typing import Annotated, Optional
from uuid import UUID

import jwt
from fastapi import Cookie, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes
from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.app.core.security import oauth2_scheme
from src.app.core.settings import settings
from src.app.models.user import User as UserModel
from src.app.utils.hashing import verify_password
from src.app.dependencies.session import SessionDep
from src.app.models.role import Role

type AuthenticatedUser = Optional[UserModel]


async def authenticate_user(
    auth_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> AuthenticatedUser:
    email = auth_data.username

    statement = (
        select(UserModel)
        .where(UserModel.email == email)
        .options(
            selectinload(UserModel.roles).selectinload(Role.permissions),
        )
    )
    result = await session.exec(statement)
    user = result.first()

    if user is None or not user.is_active:
        return None

    if verify_password(auth_data.password, user.password_hash):
        return user

    return None


AuthenticatedUserDep = Annotated[AuthenticatedUser, Depends(authenticate_user)]


def collect_user_scopes(user: UserModel) -> set[str]:
    scopes: set[str] = set()
    for role in user.roles:
        for permission in role.permissions:
            scopes.add(permission.scope)
    return scopes


async def get_user_with_roles(
    session: SessionDep,
    user_id: UUID,
) -> UserModel | None:
    statement = (
        select(UserModel)
        .where(UserModel.id == user_id)
        .options(
            selectinload(UserModel.roles).selectinload(Role.permissions),
        )
    )
    result = await session.exec(statement)
    return result.first()


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Authentication credentials were not provided or are invalid',
    )

    try:
        payload = jwt.decode(
            token,
            settings.auth.secret,
            algorithms=[settings.auth.token_algorithm],
        )
    except (jwt.InvalidTokenError, ValueError):
        raise credentials_exception

    user_id = payload.get('sub')
    if user_id is None:
        raise credentials_exception

    try:
        user = await get_user_with_roles(session, UUID(user_id))
    except ValueError:
        raise credentials_exception

    if user is None or not user.is_active:
        raise credentials_exception

    user_scopes = collect_user_scopes(user)

    for required_scope in security_scopes.scopes:
        if required_scope not in user_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Not enough permissions',
            )

    return user


CurrentUserDep = Annotated[UserModel, Depends(get_current_user)]


async def get_current_user_from_refresh_token(
    session: SessionDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> UserModel | None:
    if refresh_token is None:
        return None

    try:
        payload = jwt.decode(
            refresh_token,
            settings.auth.secret,
            algorithms=[settings.auth.token_algorithm],
        )
    except (jwt.InvalidTokenError, ValueError):
        return None

    user_id = payload.get('sub')
    if user_id is None:
        return None

    try:
        return await get_user_with_roles(session, UUID(user_id))
    except ValueError:
        return None


CurrentUserFromRefreshDep = Annotated[
    UserModel | None, Depends(get_current_user_from_refresh_token)
]