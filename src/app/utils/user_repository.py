from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlmodel import select

from src.app.dependencies.session import SessionDep
from src.app.models.role import Role
from src.app.models.user import User
from src.app.utils.repository import Repository


class UserRepository(Repository[User]):
    def __init__(self, session: SessionDep):
        super().__init__(session)
        self.__session = session

    async def get_by_email_with_roles_permissions(self, email: str) -> User | None:
        statement = (
            select(User)
            .where(User.email == email)
            .options(
                selectinload(User.roles).selectinload(Role.permissions),
            )
        )
        result = await self.__session.exec(statement)
        return result.first()

    async def get_by_id_with_roles_permissions(self, user_id: UUID) -> User | None:
        statement = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.roles).selectinload(Role.permissions),
            )
        )
        result = await self.__session.exec(statement)
        return result.first()
