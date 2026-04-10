from uuid import UUID

from src.app.core.rbac import INITIAL_ROLE_SCOPES, PERMISSION_DESCRIPTIONS
from src.app.core.settings import settings
from src.app.dependencies.repositories import (
    PermissionRepository,
    PermissionRepositoryDep,
    RolePermissionRepository,
    RolePermissionRepositoryDep,
    RoleRepository,
    RoleRepositoryDep,
    UserRepository,
    UserRepositoryDep,
    UserRoleRepository,
    UserRoleRepositoryDep,
)
from src.app.models.permission import Permission
from src.app.models.role import Role
from src.app.models.role_permission import RolePermissionLink
from src.app.models.user import User
from src.app.models.user_role import UserRoleLink
from src.app.schemas.user_filters import UserFilters
from src.app.utils.hashing import get_password_hash


class RBACBootstrapService:
    __permission_repository: PermissionRepository
    __role_repository: RoleRepository
    __role_permission_repository: RolePermissionRepository
    __user_repository: UserRepository
    __user_role_repository: UserRoleRepository

    def __init__(
        self,
        permission_repository: PermissionRepositoryDep,
        role_repository: RoleRepositoryDep,
        role_permission_repository: RolePermissionRepositoryDep,
        user_repository: UserRepositoryDep,
        user_role_repository: UserRoleRepositoryDep,
    ):
        self.__permission_repository = permission_repository
        self.__role_repository = role_repository
        self.__role_permission_repository = role_permission_repository
        self.__user_repository = user_repository
        self.__user_role_repository = user_role_repository

    async def bootstrap(self) -> None:
        print('RBAC bootstrap started')
        permissions = await self.__ensure_permissions()

        admin_role = await self.__ensure_role(settings.rbac.admin_role)
        admin_role_id = admin_role.id

        public_role = await self.__ensure_role(settings.rbac.public_role)
        admin_role_id = admin_role.id

        await self.__assign_all_permissions_to_role(admin_role.id, permissions)
        await self.__assign_scopes_to_role(
            public_role.id,
            INITIAL_ROLE_SCOPES.get(settings.rbac.public_role, []),
            permissions,
        )

        admin_user = await self.__ensure_admin_user()
        admin_role_id = admin_role.id
        await self.__assign_role_to_user(admin_user.id, admin_role.id)
        print('RBAC bootstrap finished')
    async def __ensure_permissions(self) -> dict[str, UUID]:
        existing_permissions = await self.__permission_repository.fetch(limit=1000)
        permissions_by_scope: dict[str, UUID] = {
            permission.scope: permission.id for permission in existing_permissions
        }

        for scope in PERMISSION_DESCRIPTIONS:
            if scope in permissions_by_scope:
                continue

            subject, action = scope.split(':', maxsplit=1)
            permission = Permission(subject=subject, action=action)
            permission = await self.__permission_repository.save(permission)
            permissions_by_scope[permission.scope] = permission.id

        return permissions_by_scope

    async def __ensure_role(self, role_name: str) -> Role:
        existing_role = await self.__role_repository.get_one_by_filters(
            extra_filters={'name': role_name},
        )
        if existing_role is not None:
            return existing_role

        role = Role(name=role_name)
        return await self.__role_repository.save(role)

    async def __assign_all_permissions_to_role(
        self,
        role_id: UUID,
        permissions: dict[str, UUID],
    ) -> None:
        for permission_id in permissions.values():
            await self.__ensure_role_permission_link(role_id, permission_id)

    async def __assign_scopes_to_role(
        self,
        role_id: UUID,
        scopes: list[str],
        permissions: dict[str, UUID],
    ) -> None:
        for scope in scopes:
            permission_id = permissions.get(scope)
            if permission_id is None:
                continue
            await self.__ensure_role_permission_link(role_id, permission_id)

    async def __ensure_role_permission_link(
        self,
        role_id: UUID,
        permission_id: UUID,
    ) -> None:
        existing_link = await self.__role_permission_repository.get_one_by_filters(
            extra_filters={
                'role_id': role_id,
                'permission_id': permission_id,
            },
        )
        if existing_link is not None:
            return

        link = RolePermissionLink(role_id=role_id, permission_id=permission_id)
        await self.__role_permission_repository.save(link)

    async def __ensure_admin_user(self) -> User:
        existing_admin = await self.__user_repository.get_one_by_filters(
            filters=UserFilters(email=settings.rbac.admin_email),
        )
        if existing_admin is not None:
            return existing_admin

        admin_user = User(
            email=settings.rbac.admin_email,
            username='admin',
            avatar_url=None,
            password_hash=get_password_hash(settings.rbac.admin_password),
            is_active=True,
        )
        return await self.__user_repository.save(admin_user)

    async def __assign_role_to_user(self, user_id: UUID, role_id: UUID) -> None:
        existing_link = await self.__user_role_repository.get_one_by_filters(
            extra_filters={
                'user_id': user_id,
                'role_id': role_id,
            },
        )
        if existing_link is not None:
            return

        link = UserRoleLink(user_id=user_id, role_id=role_id)
        await self.__user_role_repository.save(link)
        await self.__user_role_repository.save(link)

