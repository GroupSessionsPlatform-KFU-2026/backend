import asyncio

from sqlmodel.ext.asyncio.session import AsyncSession

from src.app.db.engine import engine
from src.app.models.permission import Permission
from src.app.models.role import Role
from src.app.models.role_permission import RolePermissionLink
from src.app.models.user import User
from src.app.models.user_role import UserRoleLink
from src.app.services.rbac_bootstrap import RBACBootstrapService
from src.app.utils.repository import Repository


async def init_rbac():
    async with AsyncSession(engine) as session:
        bootstrap_service = RBACBootstrapService(
            permission_repository=Repository[Permission](session),
            role_repository=Repository[Role](session),
            role_permission_repository=Repository[RolePermissionLink](session),
            user_repository=Repository[User](session),
            user_role_repository=Repository[UserRoleLink](session),
        )
        await bootstrap_service.bootstrap()

    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(init_rbac())