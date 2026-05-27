from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import BackgroundTasks, HTTPException, status
from fastapi_mail import MessageSchema
from src.app.core.rbac import PERMISSION_DESCRIPTIONS
from src.app.core.settings import settings
from src.app.dependencies.auth import require_scopes
from src.app.models.permission import Permission
from src.app.models.project_tag import ProjectTagCreate, ProjectTagUpdate
from src.app.models.role import Role
from src.app.models.user import User
from src.app.schemas.email import EmailSendData
from src.app.schemas.project_tag_filters import ProjectTagFilters
from src.app.services.email import EmailService
from src.app.services.project_tags import ProjectTagService
from src.app.services.rbac_bootstrap import RBACBootstrapService


class FakeRepository:
    def __init__(self, items: list[Any] | None = None) -> None:
        self.items = items or []

    async def fetch(self, *_, **__) -> list[Any]:
        return list(self.items)

    async def save(self, instance):
        if not hasattr(instance, 'id'):
            self.items.append(instance)
            return instance

        existing_index = next(
            (
                index
                for index, item in enumerate(self.items)
                if getattr(item, 'id', None) == getattr(instance, 'id', None)
            ),
            None,
        )
        if existing_index is None:
            self.items.append(instance)
        else:
            self.items[existing_index] = instance
        return instance

    async def get(self, pk: UUID):
        return next((item for item in self.items if item.id == pk), None)

    async def get_one_by_filters(self, filters=None, extra_filters=None):
        filters_dict = {}
        if filters is not None:
            filters_dict.update(filters.model_dump(exclude_unset=True))
        if extra_filters is not None:
            filters_dict.update(extra_filters)

        def matches_filters(item) -> bool:
            return all(
                getattr(item, key) == value for key, value in filters_dict.items()
            )

        return next(
            (item for item in self.items if matches_filters(item)),
            None,
        )

    async def update(self, pk: UUID, updates):
        instance = await self.get(pk)
        if instance is None:
            return None

        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(instance, key, value)
        return instance

    async def delete(self, pk: UUID):
        instance = await self.get(pk)
        if instance is None:
            return None

        self.items = [item for item in self.items if item.id != pk]
        return instance


async def test_project_tag_service_crud():
    repository = FakeRepository()
    service = ProjectTagService(repository)
    project_id = uuid4()
    tag_id = uuid4()

    created = await service.create_project_tag(
        ProjectTagCreate(project_id=project_id, tag_id=tag_id)
    )
    assert created.is_active is True

    filters = ProjectTagFilters(project_id=project_id)
    assert await service.get_project_tags(filters) == [created]

    updated_tag_id = uuid4()
    updated = await service.update_project_tag(
        ProjectTagUpdate(project_id=project_id, tag_id=updated_tag_id),
        created.id,
    )
    assert updated.tag_id == updated_tag_id

    assert (
        await service.update_project_tag(
            ProjectTagUpdate(project_id=project_id, tag_id=tag_id),
            uuid4(),
        )
        is None
    )

    deleted = await service.delete_project_tag(created.id)
    assert deleted.id == created.id
    assert await service.delete_project_tag(created.id) is None


async def test_rbac_bootstrap_creates_and_reuses_permissions_roles_and_admin():
    permission_repository = FakeRepository()
    role_repository = FakeRepository()
    role_permission_repository = FakeRepository()
    user_repository = FakeRepository()
    user_role_repository = FakeRepository()
    service = RBACBootstrapService(
        permission_repository=permission_repository,
        role_repository=role_repository,
        role_permission_repository=role_permission_repository,
        user_repository=user_repository,
        user_role_repository=user_role_repository,
    )

    await service.bootstrap()
    await service.bootstrap()

    permission_scopes = {
        f'{permission.subject}:{permission.action}'
        for permission in permission_repository.items
    }
    role_names = {role.name for role in role_repository.items}
    admin_users = [
        user
        for user in user_repository.items
        if user.email == settings.rbac.admin_email
    ]

    assert set(PERMISSION_DESCRIPTIONS).issubset(permission_scopes)
    assert {settings.rbac.admin_role, settings.rbac.public_role}.issubset(role_names)
    assert len(admin_users) == 1
    assert admin_users[0].is_verified is True
    assert len(user_role_repository.items) == 1
    assert len(role_permission_repository.items) >= len(PERMISSION_DESCRIPTIONS)


async def test_rbac_bootstrap_verifies_existing_admin_user():
    admin_user = User(
        email=settings.rbac.admin_email,
        username='admin',
        avatar_url=None,
        password_hash='hash',
        is_active=True,
        is_verified=False,
    )
    user_repository = FakeRepository([admin_user])
    service = RBACBootstrapService(
        permission_repository=FakeRepository(),
        role_repository=FakeRepository(),
        role_permission_repository=FakeRepository(),
        user_repository=user_repository,
        user_role_repository=FakeRepository(),
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
