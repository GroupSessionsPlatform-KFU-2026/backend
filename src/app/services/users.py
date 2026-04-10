from typing import Optional, Sequence
from uuid import UUID

from src.app.dependencies.repositories import UserRepository, UserRepositoryDep
from src.app.models.user import User, UserCreate, UserUpdate
from src.app.schemas.user_filters import UserFilters
from src.app.utils.hashing import get_password_hash


class UserService:
    __user_repository: UserRepository

    def __init__(self, user_repository: UserRepositoryDep):
        self.__user_repository = user_repository

    async def get_users(self, filters: UserFilters) -> Sequence[User]:
        return await self.__user_repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self.__user_repository.get_one_by_filters(
            filters=UserFilters(email=email),
        )

    async def create_user(self, user_create: UserCreate) -> User:
        user_dump = user_create.model_dump()

        password = str(user_dump.pop('password'))
        password_hash = get_password_hash(password)

        user = User(
            **user_dump,
            password_hash=password_hash,
            is_active=True,
        )

        return await self.__user_repository.save(user)

    async def get_user(self, user_id: UUID) -> Optional[User]:
        return await self.__user_repository.get(user_id)

    async def update_user(
        self,
        user_update: UserUpdate,
        user_id: UUID,
    ) -> Optional[User]:
        return await self.__user_repository.update(user_id, user_update)

    async def delete_user(self, user_id: UUID) -> Optional[User]:
        return await self.__user_repository.delete(user_id)

    async def get_me(self, user_id: UUID) -> Optional[User]:
        # TODO: replace user_id argument with OAuth current user later.
        return await self.__user_repository.get(user_id)
