from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes

from src.app.core.security import oauth2_scheme
from src.app.dependencies.services import get_auth_service
from src.app.models.user import User as UserModel
from src.app.services.auth import AuthService


async def authenticate_user(
    auth_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.authenticate_user(
        email=auth_data.username,
        password=auth_data.password,
    )


AuthenticatedUserDep = Annotated[UserModel | None, Depends(authenticate_user)]


async def get_access_token(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> str:
    return token


AccessTokenDep = Annotated[str, Depends(get_access_token)]


async def get_current_user(
    access_token: AccessTokenDep,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.get_current_user(
        token=access_token,
        required_scopes=[],
    )


CurrentUserDep = Annotated[UserModel, Depends(get_current_user)]


async def require_scoped_user(
    security_scopes: SecurityScopes,
    current_user: CurrentUserDep,
    auth_service: AuthService = Depends(get_auth_service),
):
    auth_service.ensure_user_scopes(current_user, security_scopes.scopes)
    return current_user