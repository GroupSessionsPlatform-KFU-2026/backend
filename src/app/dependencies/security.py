from typing import Annotated, Optional
from uuid import UUID

import jwt
from fastapi import Cookie, Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.app.core.security import oauth2_scheme
from src.app.core.settings import settings
from src.app.dependencies.services import UserServiceDep
from src.app.models.user import User as UserModel
from src.app.utils.hashing import verify_password

type AuthenticatedUser = Optional[UserModel]


async def authenticate_user(
    auth_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserServiceDep,
) -> AuthenticatedUser:
    email = auth_data.username
    user = await user_service.get_user_by_email(email)

    if user is None:
        return None
    password = auth_data.password
    is_password_matched = verify_password(password, user.password_hash)

    if is_password_matched:
        return user
    return None


AuthenticatedUserDep = Annotated[AuthenticatedUser, Depends(authenticate_user)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], user_service: UserServiceDep
) -> AuthenticatedUser:
    payload = jwt.decode(
        token,
        settings.auth.secret,
        algorithms=[settings.auth.token_algorithm],
    )

    user_id = payload.get('sub')
    if user_id is None:
        return None

    return await user_service.get_user(UUID(user_id))


CurrentUserDep = Annotated[AuthenticatedUser, Depends(get_current_user)]


# Здесь refresh-токен обрабатывается отдельно через cookie и
# не содержит access-токен внутри
async def get_current_user_from_refresh_token(
    refresh_token: Annotated[str | None, Cookie()] = None,
    user_service: UserServiceDep = None,
) -> AuthenticatedUser:
    if refresh_token is None:
        return None

    payload = jwt.decode(
        refresh_token,
        settings.auth.secret,
        algorithms=[settings.auth.token_algorithm],
    )

    user_id = payload.get('sub')

    if user_id is None:
        return None

    return await user_service.get_user(UUID(user_id))


CurrentUserFromRefreshDep = Annotated[
    AuthenticatedUser, Depends(get_current_user_from_refresh_token)
]
