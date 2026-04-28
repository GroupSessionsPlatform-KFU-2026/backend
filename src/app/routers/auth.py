from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Query, Request, Response, status

from src.app.core.limiter import limiter
from src.app.core.settings import settings
from src.app.dependencies.security import AuthenticatedUserDep
from src.app.dependencies.services import AuthServiceDep
from src.app.models.user import UserCreate
from src.app.schemas.errors import ErrorSchema
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


REGISTER_RESPONSES = {
    409: {
        'model': ErrorSchema,
        'description': 'Email or username already exists',
        'content': {
            'application/json': {
                'examples': {
                    'email_exists': {
                        'summary': 'Email already exists',
                        'value': {
                            'message': 'User with this email already exists',
                            'detail': {},
                        },
                    },
                    'username_exists': {
                        'summary': 'Username already exists',
                        'value': {
                            'message': 'User with this username already exists',
                            'detail': {},
                        },
                    },
                }
            }
        },
    },
    500: {
        'model': ErrorSchema,
        'description': 'Public role is not initialized',
        'content': {
            'application/json': {
                'example': {
                    'message': 'Public role is not initialized',
                    'detail': {},
                }
            }
        },
    },
}

LOGIN_RESPONSES = {
    401: {
        'model': ErrorSchema,
        'description': 'Invalid credentials',
        'content': {
            'application/json': {
                'example': {
                    'message': 'Invalid email or password',
                    'detail': {},
                }
            }
        },
    },
    403: {
        'model': ErrorSchema,
        'description': 'Account is not verified',
        'content': {
            'application/json': {
                'example': {
                    'message': 'Account is not verified',
                    'detail': {},
                }
            }
        },
    },
}

REFRESH_RESPONSES = {
    401: {
        'model': ErrorSchema,
        'description': 'Refresh token error',
        'content': {
            'application/json': {
                'examples': {
                    'not_provided': {
                        'summary': 'Refresh token was not provided',
                        'value': {
                            'message': 'Refresh token was not provided',
                            'detail': {},
                        },
                    },
                    'invalid': {
                        'summary': 'Invalid refresh token',
                        'value': {
                            'message': 'Invalid refresh token',
                            'detail': {},
                        },
                    },
                    'invalid_session': {
                        'summary': 'Refresh session is invalid',
                        'value': {
                            'message': 'Refresh session is invalid',
                            'detail': {},
                        },
                    },
                    'expired': {
                        'summary': 'Refresh token expired',
                        'value': {
                            'message': 'Refresh token expired',
                            'detail': {},
                        },
                    },
                }
            }
        },
    },
}

LOGOUT_RESPONSES = {
    401: {
        'model': ErrorSchema,
        'description': 'Refresh token error',
        'content': {
            'application/json': {
                'examples': {
                    'not_provided': {
                        'summary': 'Refresh token was not provided',
                        'value': {
                            'message': 'Refresh token was not provided',
                            'detail': {},
                        },
                    },
                    'invalid': {
                        'summary': 'Invalid refresh token',
                        'value': {
                            'message': 'Invalid refresh token',
                            'detail': {},
                        },
                    },
                }
            }
        },
    },
}

VERIFY_RESPONSES = {
    400: {
        'model': ErrorSchema,
        'description': 'Notification already used or expired',
        'content': {
            'application/json': {
                'examples': {
                    'already_used': {
                        'summary': 'Email notification already used',
                        'value': {
                            'message': 'Email notification already used',
                            'detail': {},
                        },
                    },
                    'expired': {
                        'summary': 'Email notification expired',
                        'value': {
                            'message': 'Email notification expired',
                            'detail': {},
                        },
                    },
                }
            }
        },
    },
    404: {
        'model': ErrorSchema,
        'description': 'User or email notification not found',
        'content': {
            'application/json': {
                'examples': {
                    'user_not_found': {
                        'summary': 'User not found',
                        'value': {
                            'message': 'User not found',
                            'detail': {},
                        },
                    },
                    'notification_not_found': {
                        'summary': 'Email notification not found',
                        'value': {
                            'message': 'Email notification not found',
                            'detail': {},
                        },
                    },
                }
            }
        },
    },
}

SEND_RESET_CODE_RESPONSES = {
    404: {
        'model': ErrorSchema,
        'description': 'User not found',
        'content': {
            'application/json': {
                'example': {
                    'message': 'User not found',
                    'detail': {},
                }
            }
        },
    },
}

CONFIRM_RESET_RESPONSES = {
    400: {
        'model': ErrorSchema,
        'description': 'Validation error in reset confirmation',
        'content': {
            'application/json': {
                'examples': {
                    'passwords_do_not_match': {
                        'summary': 'Passwords do not match',
                        'value': {
                            'message': 'Passwords do not match',
                            'detail': {},
                        },
                    },
                    'notification_already_used': {
                        'summary': 'Email notification already used',
                        'value': {
                            'message': 'Email notification already used',
                            'detail': {},
                        },
                    },
                    'notification_expired': {
                        'summary': 'Email notification expired',
                        'value': {
                            'message': 'Email notification expired',
                            'detail': {},
                        },
                    },
                }
            }
        },
    },
    404: {
        'model': ErrorSchema,
        'description': 'User or email notification not found',
        'content': {
            'application/json': {
                'examples': {
                    'user_not_found': {
                        'summary': 'User not found',
                        'value': {
                            'message': 'User not found',
                            'detail': {},
                        },
                    },
                    'notification_not_found': {
                        'summary': 'Email notification not found',
                        'value': {
                            'message': 'Email notification not found',
                            'detail': {},
                        },
                    },
                }
            }
        },
    },
}


@router.post(
    '/register',
    status_code=status.HTTP_201_CREATED,
    responses=REGISTER_RESPONSES,
)
@limiter.limit(settings.rate_limit.auth)
async def register(
    request: Request,
    user_create: UserCreate,
    auth_service: AuthServiceDep,
) -> RegisterResponse:
    _ = request
    return await auth_service.register(user_create)


@router.post(
    '/login',
    responses=LOGIN_RESPONSES,
)
@limiter.limit(settings.rate_limit.auth)
async def login(
    request: Request,
    response: Response,
    user: AuthenticatedUserDep,
    auth_service: AuthServiceDep,
) -> TokenData:
    _ = request
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


@router.post(
    '/refresh',
    responses=REFRESH_RESPONSES,
)
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


@router.post(
    '/logout',
    responses=LOGOUT_RESPONSES,
)
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


@router.get(
    '/user/{user_id}/verify',
    responses=VERIFY_RESPONSES,
)
async def verify_account(
    user_id: UUID,
    code: Annotated[UUID, Query()],
    auth_service: AuthServiceDep,
) -> RegisterResponse:
    return await auth_service.verify_account(user_id, code)


@router.get(
    '/user/{user_id}/password-reset/send-code',
    responses=SEND_RESET_CODE_RESPONSES,
)
async def send_password_reset_code(
    user_id: UUID,
    auth_service: AuthServiceDep,
) -> RegisterResponse:
    return await auth_service.send_password_reset_code(user_id)


@router.post(
    '/user/{user_id}/password-reset/confirm',
    responses=CONFIRM_RESET_RESPONSES,
)
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
