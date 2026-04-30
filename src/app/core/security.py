from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.app.core.rbac import PERMISSION_DESCRIPTIONS
from src.app.core.settings import settings
from src.app.models.user import User as UserModel

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='/api/v1/auth/login',
    refreshUrl='/api/v1/auth/refresh',
    scopes=PERMISSION_DESCRIPTIONS,
)


def _create_token(
    data: dict[str, Any],
    expires_delta: timedelta,
    jti: UUID,
) -> str:
    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    to_encode.update(
        {
            'iat': now,
            'exp': expire,
            'jti': str(jti),
        }
    )

    return jwt.encode(
        to_encode,
        settings.auth.secret,
        algorithm=settings.auth.token_algorithm,
    )


def create_access_token(
    user: UserModel,
    jti: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    lifetime = expires_delta or timedelta(
        seconds=settings.auth.access_token_lifetime_seconds,
    )

    return _create_token(
        data={
            'sub': str(user.id),
            'token_type': 'access',
        },
        expires_delta=lifetime,
        jti=jti,
    )


def create_refresh_token(
    user: UserModel,
    jti: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    lifetime = expires_delta or timedelta(
        seconds=settings.auth.refresh_token_lifetime_seconds,
    )

    return _create_token(
        data={
            'sub': str(user.id),
            'token_type': 'refresh',
        },
        expires_delta=lifetime,
        jti=jti,
    )


def decode_token(token: str, verify_exp: bool = True) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.auth.secret,
            algorithms=[settings.auth.token_algorithm],
            options={'verify_exp': verify_exp},
        )
    except jwt.ExpiredSignatureError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token expired',
        ) from error
    except jwt.InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
        ) from error
