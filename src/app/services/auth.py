from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from src.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.app.core.settings import settings
from src.app.dependencies.repositories import (
    RefreshSessionRepository,
    RefreshSessionRepositoryDep,
    RoleRepository,
    RoleRepositoryDep,
    UserRepository,
    UserRepositoryDep,
    UserRoleRepository,
    UserRoleRepositoryDep,
)
from src.app.models.refresh_session import RefreshSession
from src.app.models.user import User, UserCreate
from src.app.models.user_role import UserRoleLink
from src.app.schemas.security import LogoutResponse, RegisterResponse, TokenData
from src.app.schemas.user_filters import UserFilters
from src.app.services.users import UserService


class AuthService:
    __user_repository: UserRepository
    __refresh_session_repository: RefreshSessionRepository
    __role_repository: RoleRepository
    __user_role_repository: UserRoleRepository

    def __init__(
        self,
        user_repository: UserRepositoryDep,
        refresh_session_repository: RefreshSessionRepositoryDep,
        role_repository: RoleRepositoryDep,
        user_role_repository: UserRoleRepositoryDep,
        user_service: UserService,
    ):
        self.__user_repository = user_repository
        self.__refresh_session_repository = refresh_session_repository
        self.__role_repository = role_repository
        self.__user_role_repository = user_role_repository
        self.__user_service = user_service

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

        user = await self.__user_service.create_user(user_create)

        public_role = await self.__role_repository.get_one_by_filters(
            extra_filters={'name': settings.rbac.public_role},
        )
        if public_role is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Public role is not initialized',
            )

        existing_link = await self.__user_role_repository.get_one_by_filters(
            extra_filters={
                'user_id': user.id,
                'role_id': public_role.id,
            },
        )
        if existing_link is None:
            await self.__user_role_repository.save(
                UserRoleLink(user_id=user.id, role_id=public_role.id),
            )

        return RegisterResponse()

    async def authenticate_user(self, email: str, password: str) -> User | None:
        user = await self.__user_repository.get_by_email_with_roles_permissions(email)

        if user is None or not user.is_active:
            return None

        if not self.__user_service.verify_user_password(password, user.password_hash):
            return None

        return user

    async def get_current_user(
        self,
        token: str,
        required_scopes: list[str],
    ) -> User:
        payload = decode_token(token)

        if payload.get('token_type') != 'access':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Authentication credentials were not provided or are invalid',
            )

        user_id = payload.get('sub')
        access_jti = payload.get('jti')

        if user_id is None or access_jti is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Authentication credentials were not provided or are invalid',
            )

        try:
            user_uuid = UUID(str(user_id))
            access_jti_uuid = UUID(str(access_jti))
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Authentication credentials were not provided or are invalid',
            ) from error

        refresh_session = await self.__refresh_session_repository.get_one_by_filters(
            extra_filters={'access_jti': access_jti_uuid},
        )
        if (
            refresh_session is None
            or refresh_session.is_revoked
            or refresh_session.user_id != user_uuid
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Authentication credentials were not provided or are invalid',
            )

        user = await self.__user_repository.get_by_id_with_roles_permissions(user_uuid)

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Authentication credentials were not provided or are invalid',
            )

        self.ensure_user_scopes(user, required_scopes)
        return user

    async def login(self, user: User | None) -> TokenData:
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid email or password',
            )

        safe_user_id = user.id

        access_jti = uuid4()
        refresh_jti = uuid4()

        access_token = create_access_token(user, access_jti)
        refresh_token = create_refresh_token(user, refresh_jti)

        user.last_login_at = datetime.now(timezone.utc)
        await self.__user_repository.save(user)

        await self.__create_refresh_session(
            user_id=safe_user_id,
            refresh_token=refresh_token,
            refresh_jti=refresh_jti,
            access_jti=access_jti,
        )

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

        payload = decode_token(refresh_token, verify_exp=False)

        if payload.get('token_type') != 'refresh':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid refresh token',
            )

        user_id = payload.get('sub')
        refresh_jti = payload.get('jti')

        if user_id is None or refresh_jti is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid refresh token',
            )

        try:
            user_uuid = UUID(str(user_id))
            refresh_jti_uuid = UUID(str(refresh_jti))
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid refresh token',
            ) from error

        refresh_session = await self.__refresh_session_repository.get_one_by_filters(
            extra_filters={'refresh_jti': refresh_jti_uuid},
        )
        if (
            refresh_session is None
            or refresh_session.is_revoked
            or refresh_session.user_id != user_uuid
        ):
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

        user = await self.__user_repository.get(user_uuid)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User is not available',
            )

        safe_user_id = user.id

        new_access_jti = uuid4()
        new_refresh_jti = uuid4()

        access_token = create_access_token(user, new_access_jti)
        new_refresh_token = create_refresh_token(user, new_refresh_jti)

        refresh_session.is_revoked = True
        await self.__refresh_session_repository.save(refresh_session)

        await self.__create_refresh_session(
            user_id=safe_user_id,
            refresh_token=new_refresh_token,
            refresh_jti=new_refresh_jti,
            access_jti=new_access_jti,
        )

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

        payload = decode_token(refresh_token, verify_exp=False)

        if payload.get('token_type') != 'refresh':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid refresh token',
            )

        refresh_jti = payload.get('jti')

        if refresh_jti is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid refresh token',
            )

        try:
            refresh_jti_uuid = UUID(str(refresh_jti))
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid refresh token',
            ) from error

        refresh_session = await self.__refresh_session_repository.get_one_by_filters(
            extra_filters={'refresh_jti': refresh_jti_uuid},
        )

        if refresh_session is not None and not refresh_session.is_revoked:
            refresh_session.is_revoked = True
            await self.__refresh_session_repository.save(refresh_session)

        return LogoutResponse()

    def ensure_user_scopes(self, user: User, required_scopes: list[str]) -> None:
        user_scopes = self.__collect_user_scopes(user)

        for required_scope in required_scopes:
            if required_scope not in user_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Not enough permissions',
                )

    def __collect_user_scopes(self, user: User) -> set[str]:
        return {
            permission.scope for role in user.roles for permission in role.permissions
        }

    async def __create_refresh_session(
        self,
        user_id: UUID,
        refresh_token: str,
        refresh_jti: UUID,
        access_jti: UUID,
    ) -> RefreshSession:
        payload = decode_token(refresh_token)

        exp = payload.get('exp')

        if exp is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid refresh token payload',
            )

        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

        refresh_session = RefreshSession(
            user_id=user_id,
            refresh_jti=refresh_jti,
            access_jti=access_jti,
            expires_at=expires_at,
            is_revoked=False,
        )
        return await self.__refresh_session_repository.save(refresh_session)
