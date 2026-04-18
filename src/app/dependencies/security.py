from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes

from src.app.core.security import oauth2_scheme
from src.app.dependencies.services import AuthServiceDep
from src.app.models.user import User as UserModel

type AuthenticatedUser = UserModel | None


async def authenticate_user(
    auth_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep,
) -> AuthenticatedUser:
    return await auth_service.authenticate_user(
        email=auth_data.username,
        password=auth_data.password,
    )


AuthenticatedUserDep = Annotated[AuthenticatedUser, Depends(authenticate_user)]


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthServiceDep,
) -> UserModel:
    return await auth_service.get_current_user(
        token=token,
        required_scopes=security_scopes.scopes,
    )


CurrentUserUsersWriteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['users:write']),
]

CurrentProfileUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['profile:read']),
]

CurrentUsersReadUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['users:read']),
]

CurrentUserBoardReadDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['board:read']),
]

CurrentUserBoardWriteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['board:write']),
]

CurrentUserBoardDeleteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['board:delete']),
]
