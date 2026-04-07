from datetime import datetime, timezone
from uuid import UUID

import jwt
from fastapi import HTTPException, status

from src.app.core.security import create_access_token, create_refresh_token
from src.app.core.settings import settings
from src.app.dependencies.repositories import (
    RefreshSessionRepository,
    RefreshSessionRepositoryDep,
    UserRepository,
    UserRepositoryDep,
)
from src.app.models.refresh_session import RefreshSession
from src.app.models.user import User, UserCreate
from src.app.schemas.security import LogoutResponse, RegisterResponse, TokenData
from src.app.schemas.user_filters import UserFilters
from src.app.utils.hashing import get_password_hash


class AuthService:
    __user_repository: UserRepository
    __refresh_session_repository: RefreshSessionRepository

    def __init__(
        self,
        user_repository: UserRepositoryDep,
        refresh_session_repository: RefreshSessionRepositoryDep,
    ):
        self.__user_repository = user_repository
        self.__refresh_session_repository = refresh_session_repository

    async def register(self, user_create: UserCreate) -> RegisterResponse:
        existing_user_by_email = await self.__user_repository.get_one_by_filters(
            filters=UserFilters(email=user_create.email),
        )
        if existing_user_by_email is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='User with this email already exists',
            )

        existing_user_by_username = await self.__user_repository.get_one_by_filters(
            filters=UserFilters(username=user_create.username),
        )
        if existing_user_by_username is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='User with this username already exists',
            )

        user = User(
            email=user_create.email,
            username=user_create.username,
            avatar_url=user_create.avatar_url,
            password_hash=get_password_hash(user_create.password),
            is_active=True,
        )
        await self.__user_repository.save(user)

        return RegisterResponse()

    async def login(self, user: User | None) -> TokenData:
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid email or password',
            )

        safe_user_id = user.id

        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)

        user.last_login_at = datetime.now(timezone.utc)
        await self.__user_repository.save(user)

        await self.__create_refresh_session(safe_user_id, refresh_token)

        return TokenData(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type='bearer',
        )

    async def refresh(self, refresh_token: str | None) -> TokenData:
        if refresh_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Refresh token was not provided',
            )

        payload = self.__decode_token(refresh_token)

        user_id = payload.get('sub')
        jti = payload.get('jti')

        if user_id is None or jti is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid refresh token',
            )

        refresh_session = await self.__refresh_session_repository.get_one_by_filters(
            extra_filters={'jti': str(jti)},
        )
        if refresh_session is None or refresh_session.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Refresh session is invalid',
            )

        if refresh_session.expires_at <= datetime.now(timezone.utc):
            refresh_session.is_revoked = True
            await self.__refresh_session_repository.save(refresh_session)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Refresh token expired',
            )

        user = await self.__user_repository.get(UUID(user_id))
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User is not available',
            )

        refresh_session.is_revoked = True
        # IMPORTANT: save everything needed from user BEFORE commit
        safe_user_id = user.id

        access_token = create_access_token(user)
        new_refresh_token = create_refresh_token(user)

        refresh_session.is_revoked = True
        await self.__refresh_session_repository.save(refresh_session)

        await self.__create_refresh_session(safe_user_id, new_refresh_token)

        return TokenData(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type='bearer',
        )

    async def logout(self, refresh_token: str | None) -> LogoutResponse:
        if refresh_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Refresh token was not provided',
            )

        payload = self.__decode_token(refresh_token, verify_exp=False)
        jti = payload.get('jti')

        if jti is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid refresh token',
            )

        refresh_session = await self.__refresh_session_repository.get_one_by_filters(
            extra_filters={'jti': str(jti)},
        )

        if refresh_session is not None and not refresh_session.is_revoked:
            refresh_session.is_revoked = True
            await self.__refresh_session_repository.save(refresh_session)

        return LogoutResponse()

    async def __create_refresh_session(
        self,
        user_id: UUID,
        refresh_token: str,
    ) -> RefreshSession:
        payload = self.__decode_token(refresh_token)

        jti = payload.get('jti')
        exp = payload.get('exp')

        if jti is None or exp is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid refresh token payload',
            )

        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

        refresh_session = RefreshSession(
            user_id=user_id,
            jti=str(jti),
            expires_at=expires_at,
            is_revoked=False,
        )
        return await self.__refresh_session_repository.save(refresh_session)

    def __decode_token(self, token: str, verify_exp: bool = True) -> dict:
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
