from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Query, Request, Response, status, Depends
from fastapi import APIRouter, Cookie, Request, Response, status
from fastapi import APIRouter, Cookie, Response, status

from src.app.core.limiter import limiter
from src.app.core.responses import auth_responses, conflict_responses
from src.app.core.settings import settings
from src.app.dependencies.security import AuthenticatedUserDep
from src.app.dependencies.services import get_auth_service
from src.app.services.auth import AuthService
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


VERIFY_RESPONSES = {
    400: {'description': 'Notification already used or expired'},
    404: {'description': 'User or email notification not found'},
}

SEND_RESET_CODE_RESPONSES = {
    404: {'description': 'User not found'},
}

CONFIRM_RESET_RESPONSES = {
    400: {'description': 'Validation error in reset confirmation'},
    404: {'description': 'User or email notification not found'},
}


@router.post(
    '/register',
    status_code=status.HTTP_201_CREATED,
    responses=conflict_responses,
)
@limiter.limit(settings.rate_limit.auth)
async def register(
    request: Request,
    user_create: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    return await auth_service.register(user_create)


@router.post(
    '/login',
    responses=auth_responses,
)
@limiter.limit(settings.rate_limit.auth)
async def login(
    request: Request,
    response: Response,
    user: AuthenticatedUserDep,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenData:
    token_data = await auth_service.login(user)

    response.set_cookie(
        key='refresh_token',
        value=token_data.refresh_token,
        httponly=True,
        secure=settings.auth.cookie_secure,
        # secure=False,  # TODO: set True in production (HTTPS)
        samesite='lax',
        path='/',
    )

    return token_data


@router.post(
    '/refresh',
    responses=auth_responses,
)
async def refresh(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> TokenData:
    token_data = await auth_service.refresh(refresh_token)

    response.set_cookie(
        key='refresh_token',
        value=token_data.refresh_token,
        httponly=True,
        secure=settings.auth.cookie_secure,
        # secure=False,  # TODO: set True in production (HTTPS)
        samesite='lax',
        path='/',
    )

    return token_data


@router.post(
    '/logout',
    responses=auth_responses,
)
async def logout(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> LogoutResponse:
    logout_response = await auth_service.logout(refresh_token)

    response.delete_cookie(
        key='refresh_token',
        path='/',
    )

    return logout_response


@router.get(
    '/user/{user_id}/verify',
    responses=VERIFY_RESPONSES,
)
async def verify_account(
    user_id: UUID,
    code: Annotated[UUID, Query()],
    auth_service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    return await auth_service.verify_account(user_id, code)


@router.get(
    '/user/{user_id}/password-reset/send-code',
    responses=SEND_RESET_CODE_RESPONSES,
)
async def send_password_reset_code(
    user_id: UUID,
    auth_service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    return await auth_service.send_password_reset_code(user_id)


@router.post(
    '/user/{user_id}/password-reset/confirm',
    responses=CONFIRM_RESET_RESPONSES,
)
async def confirm_password_reset(
    user_id: UUID,
    payload: PasswordResetConfirmRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    return await auth_service.confirm_password_reset(
        user_id=user_id,
        code=payload.code,
        new_password=payload.new_password,
        repeat_password=payload.repeat_password,
    )