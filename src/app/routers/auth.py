from typing import Annotated

from fastapi import APIRouter, Cookie, Response, status

from src.app.dependencies.security import AuthenticatedUserDep
from src.app.services.auth import AuthService
from src.app.models.user import UserCreate
from src.app.schemas.security import LogoutResponse, RegisterResponse, TokenData
from fastapi import Depends

router = APIRouter(
    prefix='/auth',
    tags=['auth'],
)


@router.post(
    '/register',
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_create: UserCreate,
    auth_service: AuthService = Depends(),
) -> RegisterResponse:
    return await auth_service.register(user_create)

    


@router.post('/login')
async def login(
    response: Response,
    user: AuthenticatedUserDep,
    auth_service: AuthService = Depends(),
) -> TokenData:
    token_data = await auth_service.login(user)

    response.set_cookie(
        key='refresh_token',
        value=token_data.refresh_token,
        httponly=True,
        secure=False,  # TODO: set True in production (HTTPS)
        samesite='lax',
        path='/',
    )

    return token_data


@router.post('/refresh')
async def refresh(
    response: Response,
    auth_service: AuthService = Depends(),
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> TokenData:
    token_data = await auth_service.refresh(refresh_token)

    response.set_cookie(
        key='refresh_token',
        value=token_data.refresh_token,
        httponly=True,
        secure=False,  # TODO: set True in production (HTTPS)
        samesite='lax',
        path='/',
    )

    return token_data


@router.post('/logout')
async def logout(
    response: Response,
    auth_service: AuthService = Depends(),
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> LogoutResponse:
    logout_response = await auth_service.logout(refresh_token)

    response.delete_cookie(
        key='refresh_token',
        path='/',
    )

    return logout_response
