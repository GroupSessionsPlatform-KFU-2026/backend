from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi.security import OAuth2PasswordBearer

from src.app.core.settings import settings
from src.app.models.user import User as UserModel
from src.app.core.rbac import PERMISSION_DESCRIPTIONS

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='/api/v1/auth/login',
    refreshUrl='/api/v1/auth/refresh',
    scopes=PERMISSION_DESCRIPTIONS,
)


def create_access_token(user: UserModel, expires_delta: timedelta | None = None) -> str:
    to_encode: dict[str, str | datetime] = {'sub': str(user.id)}

    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(seconds=settings.auth.access_token_lifetime_seconds)

    to_encode['iat'] = now
    to_encode['exp'] = expire
    to_encode['jti'] = str(uuid4())

    return jwt.encode(
        to_encode,
        settings.auth.secret,
        algorithm=settings.auth.token_algorithm,
    )


## В данном проекте refresh-токен реализован независимо (через jti),
# в отличие от примера в репозитории, где он содержит access-токен
def create_refresh_token(
    user: UserModel,
    expires_delta: timedelta | None = None,
) -> str:

    to_encode: dict[str, str | datetime] = {'sub': str(user.id)}

    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(seconds=settings.auth.refresh_token_lifetime_seconds)

    to_encode['iat'] = now
    to_encode['exp'] = expire
    to_encode['jti'] = str(uuid4())

    return jwt.encode(
        to_encode,
        settings.auth.secret,
        algorithm=settings.auth.token_algorithm,
    )
