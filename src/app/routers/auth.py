from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Query, Response, status

from src.app.core.settings import settings
from src.app.dependencies.security import AuthenticatedUserDep
from src.app.dependencies.services import AuthServiceDep
from src.app.models.user import UserCreate
from src.app.schemas.security import (
    LogoutResponse,
    PasswordResetConfirmRequest,
    RegisterResponse,
    TokenData,
)

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
    auth_service: AuthServiceDep,
) -> RegisterResponse:
    return await auth_service.register(user_create)


@router.post('/login')
async def login(
    response: Response,
    user: AuthenticatedUserDep,
    auth_service: AuthServiceDep,
) -> TokenData:
    token_data = await auth_service.login(user)

    response.set_cookie(
        key='refresh_token',
        value=token_data.refresh_token,
        httponly=True,
        secure=settings.auth.cookie_secure,
        samesite='lax',
        path='/',
    )

    return token_data


@router.post('/refresh')
async def refresh(
    response: Response,
    auth_service: AuthServiceDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> TokenData:
    token_data = await auth_service.refresh(refresh_token)

    response.set_cookie(
        key='refresh_token',
        value=token_data.refresh_token,
        httponly=True,
        secure=settings.auth.cookie_secure,
        samesite='lax',
        path='/',
    )

    return token_data


@router.post('/logout')
async def logout(
    response: Response,
    auth_service: AuthServiceDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> LogoutResponse:
    logout_response = await auth_service.logout(refresh_token)

    response.delete_cookie(
        key='refresh_token',
        path='/',
    )

    return logout_response


@router.get('/user/{user_id}/verify')
async def verify_account(
    user_id: UUID,
    code: Annotated[UUID, Query()],
    auth_service: AuthServiceDep,
) -> RegisterResponse:
    return await auth_service.verify_account(user_id, code)


@router.get('/user/{user_id}/password-reset/send-code')
async def send_password_reset_code(
    user_id: UUID,
    auth_service: AuthServiceDep,
) -> RegisterResponse:
    return await auth_service.send_password_reset_code(user_id)


@router.post('/user/{user_id}/password-reset/confirm')
async def confirm_password_reset(
    user_id: UUID,
    payload: PasswordResetConfirmRequest,
    auth_service: AuthServiceDep,
) -> RegisterResponse:
    return await auth_service.confirm_password_reset(
        user_id=user_id,
        code=payload.code,
        new_password=payload.new_password,
        repeat_password=payload.repeat_password,
    )
