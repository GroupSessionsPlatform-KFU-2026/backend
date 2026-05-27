import asyncio

from sqlmodel.ext.asyncio.session import AsyncSession

from src.app.db.engine import engine
from src.app.dependencies.session import async_session_maker
from src.app.models.permission import Permission
from src.app.models.role import Role
from src.app.models.role_permission import RolePermissionLink
from src.app.models.user import User
from src.app.models.user_role import UserRoleLink
from src.app.services.rbac_bootstrap import RBACBootstrapService
from src.app.utils.repository import Repository


async def bootstrap_rbac(session: AsyncSession) -> None:
    bootstrap_service = RBACBootstrapService(
        permission_repository=Repository[Permission](session),
        role_repository=Repository[Role](session),
        role_permission_repository=Repository[RolePermissionLink](session),
        user_repository=Repository[User](session),
        user_role_repository=Repository[UserRoleLink](session),
    )
    await bootstrap_service.bootstrap()


async def init_rbac(session: AsyncSession | None = None) -> None:
    if session is not None:
        await bootstrap_rbac(session)
        return

    async with async_session_maker() as default_session:
        await bootstrap_rbac(default_session)
    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(init_rbac())
