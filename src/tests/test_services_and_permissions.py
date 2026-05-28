from uuid import uuid4

import pytest
from fastapi import BackgroundTasks, HTTPException, status
from fastapi_mail import MessageSchema
from src.app.core.rbac import PERMISSION_DESCRIPTIONS
from src.app.core.settings import settings
from src.app.dependencies.auth import require_scopes
from src.app.models.permission import Permission
from src.app.models.project import Project
from src.app.models.project_tag import ProjectTag, ProjectTagCreate, ProjectTagUpdate
from src.app.models.role import Role
from src.app.models.role_permission import RolePermissionLink
from src.app.models.tag import Tag
from src.app.models.user import User
from src.app.models.user_role import UserRoleLink
from src.app.schemas.email import EmailSendData
from src.app.schemas.project_tag_filters import ProjectTagFilters
from src.app.services.email import EmailService
from src.app.services.project_tags import ProjectTagService
from src.app.services.rbac_bootstrap import RBACBootstrapService
from src.app.utils.repository import Repository


async def test_project_tag_service_crud(session_maker):
    async with session_maker() as session:
        user_repository = Repository[User](session)
        project_repository = Repository[Project](session)
        tag_repository = Repository[Tag](session)
        repository = Repository[ProjectTag](session)
        service = ProjectTagService(repository)

        owner = await user_repository.save(
            User(
                email=f'project-tag-owner-{uuid4().hex}@example.com',
                username=f'project-tag-owner-{uuid4().hex}',
                avatar_url=None,
                password_hash='hash',
                is_active=True,
                is_verified=True,
            )
        )
        project = await project_repository.save(
            Project(
                title='Project tag service',
                description=None,
                required_roles=[],
                owner_id=owner.id,
                is_archived=False,
            )
        )
        tag = await tag_repository.save(
            Tag(
                name=f'project-tag-{uuid4().hex}',
                color='#112233',
                description='Tag for project tag service',
            )
        )

        created = await service.create_project_tag(
            ProjectTagCreate(project_id=project.id, tag_id=tag.id)
        )
        assert created.is_active is True

        filters = ProjectTagFilters(project_id=project.id)
        assert await service.get_project_tags(filters) == [created]

        updated_tag = await tag_repository.save(
            Tag(
                name=f'project-tag-updated-{uuid4().hex}',
                color='#445566',
                description='Updated tag',
            )
        )
        updated = await service.update_project_tag(
            ProjectTagUpdate(project_id=project.id, tag_id=updated_tag.id),
            created.id,
        )
        assert updated.tag_id == updated_tag.id

        assert (
            await service.update_project_tag(
                ProjectTagUpdate(project_id=project.id, tag_id=tag.id),
                uuid4(),
            )
            is None
        )

        deleted = await service.delete_project_tag(created.id)
        assert deleted.id == created.id
        assert await service.delete_project_tag(created.id) is None


async def test_rbac_bootstrap_creates_and_reuses_permissions_roles_and_admin(
    session_maker,
):
    async with session_maker() as session:
        permission_repository = Repository[Permission](session)
        role_repository = Repository[Role](session)
        role_permission_repository = Repository[RolePermissionLink](session)
        user_repository = Repository[User](session)
        user_role_repository = Repository[UserRoleLink](session)
        service = RBACBootstrapService(
            permission_repository=permission_repository,
            role_repository=role_repository,
            role_permission_repository=role_permission_repository,
            user_repository=user_repository,
            user_role_repository=user_role_repository,
        )

        await service.bootstrap()
        await service.bootstrap()

        permissions = await permission_repository.fetch(limit=1000)
        roles = await role_repository.fetch(limit=1000)
        admin_users = await user_repository.fetch(
            extra_filters={'email': settings.rbac.admin_email},
        )
        user_roles = await user_role_repository.fetch(limit=1000)
        role_permissions = await role_permission_repository.fetch(limit=1000)
        permission_scopes = {
            f'{permission.subject}:{permission.action}' for permission in permissions
        }
        role_names = {role.name for role in roles}

        assert set(PERMISSION_DESCRIPTIONS).issubset(permission_scopes)
        assert {settings.rbac.admin_role, settings.rbac.public_role}.issubset(
            role_names
        )
        assert len(admin_users) == 1
        assert admin_users[0].is_verified is True
        assert len(user_roles) >= 1
        assert len(role_permissions) >= len(PERMISSION_DESCRIPTIONS)


async def test_rbac_bootstrap_verifies_existing_admin_user(session_maker):
    async with session_maker() as session:
        user_repository = Repository[User](session)
        admin_user = await user_repository.get_one_by_filters(
            extra_filters={'email': settings.rbac.admin_email}
        )
        assert admin_user is not None
        admin_user.is_verified = False
        await user_repository.save(admin_user)
        service = RBACBootstrapService(
            permission_repository=Repository[Permission](session),
            role_repository=Repository[Role](session),
            role_permission_repository=Repository[RolePermissionLink](session),
            user_repository=user_repository,
            user_role_repository=Repository[UserRoleLink](session),
        )

        ensured_admin = await service._RBACBootstrapService__ensure_admin_user()

        assert ensured_admin.id == admin_user.id
        assert ensured_admin.is_verified is True


async def test_require_scopes_allows_and_rejects_users():
    permission = Permission(subject='rooms', action='read')
    role = Role(name='public')
    role.permissions = [permission]
    user = User(
        email='scoped@example.com',
        username='scoped',
        avatar_url=None,
        password_hash='hash',
        is_active=True,
        is_verified=True,
    )
    user.roles = [role]

    checker = require_scopes(['rooms:read'])
    assert await checker(user) == user

    with pytest.raises(HTTPException) as error:
        await require_scopes(['rooms:delete'])(user)
    assert error.value.status_code == status.HTTP_403_FORBIDDEN
    assert error.value.detail == 'Not enough permissions'


async def test_email_service_schedules_and_safely_handles_errors(monkeypatch):
    background_tasks = BackgroundTasks()
    monkeypatch.setattr(settings.email, 'use_credentials', False)
    monkeypatch.setattr(settings.email, 'template_folder', 'app/templates')
    service = EmailService(background_tasks=background_tasks)

    email_data = EmailSendData(
        email_to='user@example.com',
        subject='Verify account',
        template_name='verify.html',
        body={'code': '1234'},
    )

    service.send_email(email_data)
    assert len(background_tasks.tasks) == 1

    class BrokenFastMail:
        async def send_message(self, _message, _template_name):
            raise ValueError('SMTP failed')

    service._fast_mail = BrokenFastMail()
    await service._send_email_safely(
        MessageSchema(
            subject=email_data.subject,
            recipients=[email_data.email_to],
            template_body=email_data.body,
            subtype='html',
        ),
        email_data.template_name,
        email_data.email_to,
    )


def test_email_service_skips_when_smtp_password_is_missing(monkeypatch):
    background_tasks = BackgroundTasks()
    monkeypatch.setattr(settings.email, 'use_credentials', True)
    monkeypatch.setattr(settings.email, 'password', '')
    monkeypatch.setattr(settings.email, 'template_folder', 'app/templates')
    service = EmailService(background_tasks=background_tasks)

    service.send_email(
        EmailSendData(
            email_to='user@example.com',
            subject='Verify account',
            template_name='verify.html',
            body={'code': '1234'},
        )
    )

    assert background_tasks.tasks == []
