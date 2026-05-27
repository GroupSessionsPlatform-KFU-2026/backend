from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, status
from src.app.core.security import (
    create_refresh_token,
    decode_token,
)
from src.app.core.settings import settings
from src.app.models.email import EmailAction, EmailNotification
from src.app.models.permission import Permission
from src.app.models.project import ProjectCreate, ProjectUpdate
from src.app.models.refresh_session import RefreshSession
from src.app.models.role import Role
from src.app.models.room import RoomCreate, RoomStatus, RoomUpdate
from src.app.models.room_participant import (
    RoomParticipantCreate,
    RoomParticipantUpdate,
)
from src.app.models.tag import Tag
from src.app.models.user import User, UserCreate
from src.app.models.user_role import UserRoleLink
from src.app.schemas.project_filters import ProjectFilters
from src.app.schemas.room_filters import RoomFilters
from src.app.schemas.room_participant_filters import RoomParticipantFilters
from src.app.schemas.room_request import JoinRoomRequest
from src.app.services.auth import AuthService
from src.app.services.projects import ProjectService
from src.app.services.room_participants import RoomParticipantService
from src.app.services.rooms import RoomService
from src.app.services.users import UserService
from src.app.utils.hashing import get_password_hash
from src.tests.test_domain_services import InMemoryRepository

pytestmark = pytest.mark.asyncio

ROOM_MAX_PARTICIPANTS = 2


class AuthUserRepository(InMemoryRepository):
    async def get_by_email_with_roles_permissions(self, email: str):
        return await self.get_one_by_filters(extra_filters={'email': email})

    async def get_by_id_with_roles_permissions(self, user_id: UUID):
        return await self.get(user_id)


class RefreshSessionRepository(InMemoryRepository):
    async def save_all(self, instances: list[RefreshSession]):
        for instance in instances:
            await self.save(instance)
        return instances


class UserRoleRepository:
    def __init__(self, items: list[UserRoleLink] | None = None) -> None:
        self.items = items or []

    async def get_one_by_filters(
        self,
        filters=None,
        extra_filters: dict[str, Any] | None = None,
    ):
        filters_dict = {}
        if filters is not None:
            filters_dict.update(filters.model_dump(exclude_unset=True))
        if extra_filters is not None:
            filters_dict.update(extra_filters)

        return next(
            (
                item
                for item in self.items
                if all(
                    getattr(item, key) == value for key, value in filters_dict.items()
                )
            ),
            None,
        )

    async def save(self, instance: UserRoleLink):
        existing_link = await self.get_one_by_filters(
            extra_filters={
                'user_id': instance.user_id,
                'role_id': instance.role_id,
            },
        )
        if existing_link is None:
            self.items.append(instance)
        return instance


class RecordingEmailService:
    def __init__(self) -> None:
        self.messages = []

    def send_email(self, email_data) -> None:
        self.messages.append(email_data)


def build_auth_service(
    users: list[User] | None = None,
    public_role: Role | None = None,
):
    user_repository = AuthUserRepository(users)
    refresh_repository = RefreshSessionRepository()
    role_items = [public_role] if public_role is not None else []
    role_repository = InMemoryRepository(role_items)
    user_role_repository = UserRoleRepository()
    email_notification_repository = InMemoryRepository()
    email_service = RecordingEmailService()

    service = AuthService(
        user_repository=user_repository,
        refresh_session_repository=refresh_repository,
        role_repository=role_repository,
        user_role_repository=user_role_repository,
        email_notification_repository=email_notification_repository,
        user_service=UserService(user_repository),
        email_service=email_service,
    )

    return {
        'service': service,
        'users': user_repository,
        'refresh_sessions': refresh_repository,
        'roles': role_repository,
        'user_roles': user_role_repository,
        'emails': email_notification_repository,
        'email_service': email_service,
    }


def build_verified_user(email: str = 'auth-user@example.com') -> User:
    return User(
        email=email,
        username=email.split('@', maxsplit=1)[0],
        avatar_url=None,
        password_hash=get_password_hash('test-password-123'),
        is_active=True,
        is_verified=True,
    )


async def test_project_service_tags_archive_and_owner_guards():
    owner_id = uuid4()
    other_user_id = uuid4()
    tag = Tag(name='backend', color='#123456', description='Backend tag')
    project_repository = InMemoryRepository()
    project_tag_repository = InMemoryRepository()

    service = ProjectService(
        project_repository=project_repository,
        project_tag_repository=project_tag_repository,
        tag_repository=InMemoryRepository([tag]),
    )

    project = await service.create_project(
        ProjectCreate(
            title='Test project',
            description='Project for service tests',
            required_roles=['backend'],
        ),
        owner_id=owner_id,
    )
    assert project.owner_id == owner_id
    assert project.is_archived is False

    with pytest.raises(HTTPException) as owner_error:
        await service.get_project(project.id, other_user_id)
    assert owner_error.value.status_code == status.HTTP_404_NOT_FOUND

    updated = await service.update_project(
        ProjectUpdate(title='Updated project'),
        project.id,
        owner_id,
    )
    assert updated.title == 'Updated project'

    relation = await service.assign_tag_to_project(project.id, tag.id, owner_id)
    assert relation.project_id == project.id
    assert relation.tag_id == tag.id
    assert await service.assign_tag_to_project(project.id, tag.id, owner_id) == relation
    assert await service.get_project_tags(project.id, owner_id) == [relation]
    assert await service.count_project_tags(project.id) == 1

    removed_relation = await service.remove_tag_from_project(
        project.id,
        tag.id,
        owner_id,
    )
    assert removed_relation == relation

    with pytest.raises(HTTPException) as relation_error:
        await service.remove_tag_from_project(project.id, tag.id, owner_id)
    assert relation_error.value.status_code == status.HTTP_404_NOT_FOUND

    with pytest.raises(HTTPException) as tag_error:
        await service.assign_tag_to_project(project.id, uuid4(), owner_id)
    assert tag_error.value.status_code == status.HTTP_404_NOT_FOUND

    archived = await service.archive_project(project.id, owner_id)
    assert archived.is_archived is True
    assert await service.count_projects(ProjectFilters(owner_id=owner_id)) == 1


async def test_room_service_lifecycle_join_rules_and_pomodoro_creation():
    creator_id = uuid4()
    participant_id = uuid4()
    second_participant_id = uuid4()
    project_id = uuid4()
    room_repository = InMemoryRepository()
    participant_repository = InMemoryRepository()
    pomodoro_repository = InMemoryRepository()
    service = RoomService(
        room_repository=room_repository,
        room_participant_repository=participant_repository,
        pomodoro_repository=pomodoro_repository,
    )

    room = await service.create_room(
        RoomCreate(
            title='Planning room',
            max_participants=ROOM_MAX_PARTICIPANTS,
            project_id=project_id,
        ),
        creator_id=creator_id,
    )
    assert room.status == RoomStatus.ACTIVE
    assert room.room_code
    assert pomodoro_repository.items[0].room_id == room.id
    assert await service.get_room(room.id) == room
    assert await service.count_rooms(RoomFilters(project_id=project_id)) == 1

    updated = await service.update_room(
        RoomUpdate(title='Daily room', max_participants=ROOM_MAX_PARTICIPANTS),
        room.id,
        creator_id,
    )
    assert updated.title == 'Daily room'

    with pytest.raises(HTTPException) as update_error:
        await service.update_room(
            RoomUpdate(title='Forbidden room', max_participants=ROOM_MAX_PARTICIPANTS),
            room.id,
            participant_id,
        )
    assert update_error.value.status_code == status.HTTP_403_FORBIDDEN

    first_join = await service.join_room(
        JoinRoomRequest(room_code=room.room_code),
        participant_id,
    )
    assert first_join.role == 'participant'
    assert (
        await service.join_room(
            JoinRoomRequest(room_code=room.room_code),
            participant_id,
        )
        == first_join
    )

    room.max_participants = 1
    with pytest.raises(HTTPException) as full_room_error:
        await service.join_room(
            JoinRoomRequest(room_code=room.room_code),
            second_participant_id,
        )
    assert full_room_error.value.status_code == status.HTTP_409_CONFLICT

    with pytest.raises(HTTPException) as missing_room_error:
        await service.join_room(JoinRoomRequest(room_code='MISSING'), uuid4())
    assert missing_room_error.value.status_code == status.HTTP_404_NOT_FOUND

    ended = await service.end_room(room.id, creator_id)
    assert ended.status == RoomStatus.ENDED
    assert ended.ended_at is not None

    with pytest.raises(HTTPException) as ended_join_error:
        await service.join_room(
            JoinRoomRequest(room_code=room.room_code),
            second_participant_id,
        )
    assert ended_join_error.value.status_code == status.HTTP_409_CONFLICT

    with pytest.raises(HTTPException) as ended_update_error:
        await service.update_room(
            RoomUpdate(title='Late update', max_participants=ROOM_MAX_PARTICIPANTS),
            room.id,
            creator_id,
        )
    assert ended_update_error.value.status_code == status.HTTP_409_CONFLICT

    with pytest.raises(HTTPException) as ended_again_error:
        await service.end_room(room.id, creator_id)
    assert ended_again_error.value.status_code == status.HTTP_409_CONFLICT


async def test_room_participant_service_updates_remove_and_missing_errors():
    room_id = uuid4()
    user_id = uuid4()
    repository = InMemoryRepository()
    service = RoomParticipantService(repository)

    participant = await service.create_participant(
        RoomParticipantCreate(room_id=room_id, user_id=user_id),
    )
    assert participant.role == 'participant'
    assert participant.left_at is None
    assert await service.get_participant_in_room(room_id, user_id) == participant
    assert await service.get_participants(
        room_id,
        RoomParticipantFilters(user_id=user_id),
    ) == [participant]
    assert await service.count_participants(room_id, RoomParticipantFilters()) == 1

    updated = await service.update_participant(
        room_id,
        user_id,
        RoomParticipantUpdate(role='moderator', is_kicked=True),
    )
    assert updated.role == 'moderator'
    assert updated.is_kicked is True

    removed = await service.remove_participant(room_id, user_id)
    assert removed.left_at is not None

    with pytest.raises(HTTPException) as missing_error:
        await service.get_participant_in_room(room_id, uuid4())
    assert missing_error.value.status_code == status.HTTP_404_NOT_FOUND


async def test_auth_service_register_duplicate_role_and_email_paths():
    existing_user = build_verified_user()
    public_role = Role(name=settings.rbac.public_role)
    context = build_auth_service(users=[existing_user], public_role=public_role)
    service = context['service']

    with pytest.raises(HTTPException) as email_error:
        await service.register(
            UserCreate(
                email=existing_user.email,
                username='new-username',
                avatar_url=None,
                password='test-password-123',
            )
        )
    assert email_error.value.status_code == status.HTTP_409_CONFLICT

    with pytest.raises(HTTPException) as username_error:
        await service.register(
            UserCreate(
                email='new-user@example.com',
                username=existing_user.username,
                avatar_url=None,
                password='test-password-123',
            )
        )
    assert username_error.value.status_code == status.HTTP_409_CONFLICT

    missing_role_context = build_auth_service()
    with pytest.raises(HTTPException) as role_error:
        await missing_role_context['service'].register(
            UserCreate(
                email='without-role@example.com',
                username='without-role',
                avatar_url=None,
                password='test-password-123',
            )
        )
    assert role_error.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    success_context = build_auth_service(public_role=public_role)
    response = await success_context['service'].register(
        UserCreate(
            email='success-register@example.com',
            username='success-register',
            avatar_url=None,
            password='test-password-123',
        )
    )
    assert response.success is True
    assert len(success_context['user_roles'].items) == 1
    assert len(success_context['emails'].items) == 1
    assert success_context['emails'].items[0].action == EmailAction.VERIFY_ACCOUNT
    assert len(success_context['email_service'].messages) == 1


async def test_auth_service_refresh_logout_and_current_user_edges():
    permission = Permission(subject='projects', action='read')
    role = Role(name=settings.rbac.public_role)
    role.permissions = [permission]
    user = build_verified_user()
    user.roles = [role]
    context = build_auth_service(users=[user], public_role=role)
    service = context['service']

    assert await service.authenticate_user(user.email, 'test-password-123') == user
    assert await service.authenticate_user(user.email, 'wrong-password') is None

    tokens = await service.login(user)
    access_payload = decode_token(tokens.access_token)
    stored_session = await context['refresh_sessions'].get_one_by_filters(
        extra_filters={'access_jti': UUID(access_payload['jti'])},
    )
    assert stored_session is not None
    assert user.last_login_at is not None

    current_user = await service.get_current_user(
        tokens.access_token,
        required_scopes=['projects:read'],
    )
    assert current_user == user

    with pytest.raises(HTTPException) as scope_error:
        await service.get_current_user(
            tokens.access_token,
            required_scopes=['projects:write'],
        )
    assert scope_error.value.status_code == status.HTTP_403_FORBIDDEN

    await service.logout(tokens.refresh_token)
    assert stored_session.is_revoked is True

    with pytest.raises(HTTPException) as revoked_access_error:
        await service.get_current_user(
            tokens.access_token,
            required_scopes=['projects:read'],
        )
    assert revoked_access_error.value.status_code == status.HTTP_401_UNAUTHORIZED

    expired_refresh_token = create_refresh_token(
        user,
        uuid4(),
        expires_delta=timedelta(seconds=-1),
    )
    expired_payload = decode_token(expired_refresh_token, verify_exp=False)
    expired_session = RefreshSession(
        user_id=user.id,
        refresh_jti=UUID(expired_payload['jti']),
        access_jti=uuid4(),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        is_revoked=False,
    )
    await context['refresh_sessions'].save(expired_session)

    with pytest.raises(HTTPException) as expired_error:
        await service.refresh(expired_refresh_token)
    assert expired_error.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert expired_session.is_revoked is True

    inactive_user = build_verified_user('inactive-user@example.com')
    inactive_user.is_active = False
    inactive_context = build_auth_service(users=[inactive_user], public_role=role)
    inactive_service = inactive_context['service']
    inactive_refresh_token = create_refresh_token(inactive_user, uuid4())
    inactive_payload = decode_token(inactive_refresh_token)
    await inactive_context['refresh_sessions'].save(
        RefreshSession(
            user_id=inactive_user.id,
            refresh_jti=UUID(inactive_payload['jti']),
            access_jti=uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            is_revoked=False,
        )
    )

    with pytest.raises(HTTPException) as inactive_error:
        await inactive_service.refresh(inactive_refresh_token)
    assert inactive_error.value.status_code == status.HTTP_401_UNAUTHORIZED


async def test_auth_service_verify_and_password_reset_notification_edges():
    user = build_verified_user('verify-reset@example.com')
    context = build_auth_service(users=[user], public_role=Role(name='public'))
    service = context['service']

    await service.send_password_reset_code(user.id)
    reset_notification = context['emails'].items[0]
    assert reset_notification.action == EmailAction.CHANGE_PASSWORD
    assert len(context['email_service'].messages) == 1

    await service.confirm_password_reset(
        user.id,
        reset_notification.code,
        new_password='new-password-123',
        repeat_password='new-password-123',
    )
    assert reset_notification.is_used is True

    with pytest.raises(HTTPException) as reused_error:
        await service.confirm_password_reset(
            user.id,
            reset_notification.code,
            new_password='other-password-123',
            repeat_password='other-password-123',
        )
    assert reused_error.value.status_code == status.HTTP_400_BAD_REQUEST

    await service.send_password_reset_code(user.id)
    expired_notification = context['emails'].items[-1]
    expired_notification.expired_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    with pytest.raises(HTTPException) as expired_error:
        await service.confirm_password_reset(
            user.id,
            expired_notification.code,
            new_password='expired-password-123',
            repeat_password='expired-password-123',
        )
    assert expired_error.value.status_code == status.HTTP_400_BAD_REQUEST

    verify_notification = await context['emails'].save(
        EmailNotification(
            user_id=user.id,
            action=EmailAction.VERIFY_ACCOUNT,
        )
    )
    verify_response = await service.verify_account(user.id, verify_notification.code)
    assert verify_response.success is True
    assert verify_notification.is_used is True

    with pytest.raises(HTTPException) as missing_user_error:
        await service.send_password_reset_code(uuid4())
    assert missing_user_error.value.status_code == status.HTTP_404_NOT_FOUND
