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

REGISTER_RESPONSES = {
    409: {
        'description': 'Email or username already exists',
        'content': {
            'application/json': {
                'examples': {
                    'email_exists': {
                        'summary': 'Email already exists',
                        'value': {
                            'detail': 'User with this email already exists',
                        },
                    },
                    'username_exists': {
                        'summary': 'Username already exists',
                        'value': {
                            'detail': 'User with this username already exists',
                        },
                    },
                }
            }
        },
    },
    500: {
        'description': 'Public role is not initialized',
        'content': {
            'application/json': {
                'example': {
                    'detail': 'Public role is not initialized',
                }
            }
        },
    },
}

LOGIN_RESPONSES = {
    401: {
        'description': 'Invalid credentials',
        'content': {
            'application/json': {
                'example': {
                    'detail': 'Invalid email or password',
                }
            }
        },
    },
    403: {
        'description': 'Account is not verified',
        'content': {
            'application/json': {
                'example': {
                    'detail': 'Account is not verified',
                }
            }
        },
    },
}

REFRESH_RESPONSES = {
    401: {
        'description': 'Refresh token error',
        'content': {
            'application/json': {
                'examples': {
                    'not_provided': {
                        'summary': 'Refresh token was not provided',
                        'value': {
                            'detail': 'Refresh token was not provided',
                        },
                    },
                    'invalid': {
                        'summary': 'Invalid refresh token',
                        'value': {
                            'detail': 'Invalid refresh token',
                        },
                    },
                    'invalid_session': {
                        'summary': 'Refresh session is invalid',
                        'value': {
                            'detail': 'Refresh session is invalid',
                        },
                    },
                    'expired': {
                        'summary': 'Refresh token expired',
                        'value': {
                            'detail': 'Refresh token expired',
                        },
                    },
                }
            }
        },
    },
}

LOGOUT_RESPONSES = {
    401: {
        'description': 'Refresh token error',
        'content': {
            'application/json': {
                'examples': {
                    'not_provided': {
                        'summary': 'Refresh token was not provided',
                        'value': {
                            'detail': 'Refresh token was not provided',
                        },
                    },
                    'invalid': {
                        'summary': 'Invalid refresh token',
                        'value': {
                            'detail': 'Invalid refresh token',
                        },
                    },
                }
            }
        },
    },
}

VERIFY_RESPONSES = {
    404: {
        'description': 'User or email notification not found',
        'content': {
            'application/json': {
                'examples': {
                    'user_not_found': {
                        'summary': 'User not found',
                        'value': {
                            'detail': 'User not found',
                        },
                    },
                    'notification_not_found': {
                        'summary': 'Email notification not found',
                        'value': {
                            'detail': 'Email notification not found',
                        },
                    },
                }
            }
        },
    },
    400: {
        'description': 'Notification already used or expired',
        'content': {
            'application/json': {
                'examples': {
                    'already_used': {
                        'summary': 'Email notification already used',
                        'value': {
                            'detail': 'Email notification already used',
                        },
                    },
                    'expired': {
                        'summary': 'Email notification expired',
                        'value': {
                            'detail': 'Email notification expired',
                        },
                    },
                }
            }
        },
    },
}

SEND_RESET_CODE_RESPONSES = {
    404: {
        'description': 'User not found',
        'content': {
            'application/json': {
                'example': {
                    'detail': 'User not found',
                }
            }
        },
    },
}

CONFIRM_RESET_RESPONSES = {
    400: {
        'description': 'Validation error in reset confirmation',
        'content': {
            'application/json': {
                'examples': {
                    'passwords_do_not_match': {
                        'summary': 'Passwords do not match',
                        'value': {
                            'detail': 'Passwords do not match',
                        },
                    },
                    'already_used': {
                        'summary': 'Email notification already used',
                        'value': {
                            'detail': 'Email notification already used',
                        },
                    },
                    'expired': {
                        'summary': 'Email notification expired',
                        'value': {
                            'detail': 'Email notification expired',
                        },
                    },
                }
            }
        },
    },
    404: {
        'description': 'User or email notification not found',
        'content': {
            'application/json': {
                'examples': {
                    'user_not_found': {
                        'summary': 'User not found',
                        'value': {
                            'detail': 'User not found',
                        },
                    },
                    'notification_not_found': {
                        'summary': 'Email notification not found',
                        'value': {
                            'detail': 'Email notification not found',
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
async def register(
    user_create: UserCreate,
    auth_service: AuthServiceDep,
) -> RegisterResponse:
    return await auth_service.register(user_create)


@router.post(
    '/login',
    responses=LOGIN_RESPONSES,
)
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
