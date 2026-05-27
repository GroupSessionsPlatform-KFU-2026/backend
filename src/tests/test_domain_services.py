from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException, status
from src.app.models.board_element import BoardElement
from src.app.models.board_element_comment import BoardElementComment
from src.app.models.chat_message import ChatMessage
from src.app.models.pomodoro_session import (
    PomodoroPhase,
    PomodoroSessionCreate,
    PomodoroSessionUpdate,
)
from src.app.models.room import Room, RoomStatus
from src.app.models.room_participant import RoomParticipant
from src.app.models.user import UserCreate, UserUpdate
from src.app.schemas.board_elements_filters import BoardElementType
from src.app.schemas.pomodoro_session_filters import PomodoroSessionFilter
from src.app.schemas.user_filters import UserFilters
from src.app.services.pomodoro_sessions import PomodoroSessionService
from src.app.services.room_access import RoomAccessService
from src.app.services.users import UserService

UPDATED_WORK_DURATION = 30


class InMemoryRepository:
    def __init__(self, items: list[Any] | None = None) -> None:
        self.items = items or []

    async def get(self, pk: UUID):
        return next((item for item in self.items if item.id == pk), None)

    async def fetch(
        self,
        filters=None,
        offset: int | None = None,
        limit: int | None = None,
        extra_filters: dict[str, Any] | None = None,
    ):
        filters_dict = {}
        if filters is not None:
            filters_dict.update(filters.model_dump(exclude_unset=True))
        if extra_filters is not None:
            filters_dict.update(extra_filters)

        for key in ('offset', 'limit'):
            filters_dict.pop(key, None)

        items = [
            item
            for item in self.items
            if all(getattr(item, key) == value for key, value in filters_dict.items())
        ]

        if offset is not None:
            items = items[offset:]
        if limit is not None:
            items = items[:limit]
        return items

    async def get_one_by_filters(self, filters=None, extra_filters=None):
        items = await self.fetch(filters=filters, limit=1, extra_filters=extra_filters)
        return items[0] if items else None

    async def count(self, filters=None, extra_filters=None) -> int:
        return len(await self.fetch(filters=filters, extra_filters=extra_filters))

    async def save(self, instance):
        existing_index = next(
            (index for index, item in enumerate(self.items) if item.id == instance.id),
            None,
        )
        if existing_index is None:
            self.items.append(instance)
        else:
            self.items[existing_index] = instance
        return instance

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


async def test_user_service_crud_and_password_checks():
    repository = InMemoryRepository()
    service = UserService(repository)

    created_user = await service.create_user(
        UserCreate(
            email='user-service@example.com',
            username='user-service',
            avatar_url=None,
            password='test-password-123',
        )
    )

    assert created_user.is_active is True
    assert created_user.password_hash != 'test-password-123'
    assert service.verify_user_password('test-password-123', created_user.password_hash)
    assert not service.verify_user_password('bad-password', created_user.password_hash)

    assert await service.get_user_by_email(created_user.email) == created_user
    assert await service.get_user(created_user.id) == created_user
    assert await service.get_me(created_user.id) == created_user
    assert await service.get_users(UserFilters(email=created_user.email)) == [
        created_user
    ]

    updated_user = await service.update_user(
        UserUpdate(username='updated-user-service'),
        created_user.id,
    )
    assert updated_user.username == 'updated-user-service'

    assert await service.delete_user(created_user.id) == updated_user
    assert await service.get_user(created_user.id) is None


async def test_pomodoro_service_lifecycle_and_missing_session_errors():
    room_id = uuid4()
    repository = InMemoryRepository()
    service = PomodoroSessionService(repository)

    created = await service.create_pomodoro(
        PomodoroSessionCreate(
            room_id=room_id,
            work_duration=25,
            short_break_duration=5,
            long_break_duration=15,
            cycles_before_long=4,
        )
    )

    assert created.current_phase == PomodoroPhase.WORK
    assert created.completed_cycles == 0
    assert created.is_running is False
    assert await service.get_pomodoro(created.id) == created
    assert await service.get_room_pomodoro(room_id) == created
    assert await service.get_pomodoros(PomodoroSessionFilter(room_id=room_id)) == [
        created
    ]

    updated = await service.update_room_pomodoro(
        room_id,
        PomodoroSessionUpdate(
            work_duration=30,
            short_break_duration=10,
            long_break_duration=20,
            cycles_before_long=3,
        ),
    )
    assert updated.work_duration == UPDATED_WORK_DURATION

    updated.current_phase = PomodoroPhase.SHORT_BREAK
    started = await service.start_pomodoro(room_id)
    assert started.is_running is True
    assert started.phase_ends_at is not None

    paused = await service.pause_pomodoro(room_id)
    assert paused.is_running is False

    reset = await service.reset_pomodoro(room_id)
    assert reset.current_phase == PomodoroPhase.WORK
    assert reset.completed_cycles == 0
    assert reset.phase_ends_at is None

    with pytest.raises(HTTPException) as error:
        await service.get_pomodoro(uuid4())
    assert error.value.status_code == status.HTTP_404_NOT_FOUND

    with pytest.raises(HTTPException) as room_error:
        await service.get_room_pomodoro(uuid4())
    assert room_error.value.status_code == status.HTTP_404_NOT_FOUND


async def test_room_access_service_roles_and_resource_ownership():
    room_id = uuid4()
    owner_id = uuid4()
    participant_id = uuid4()
    moderator_id = uuid4()
    other_author_id = uuid4()
    message_id = uuid4()
    element_id = uuid4()
    comment_id = uuid4()

    room = Room(
        id=room_id,
        title='Access room',
        max_participants=5,
        project_id=uuid4(),
        creator_id=owner_id,
        room_code='ABC123',
        status=RoomStatus.ACTIVE,
        ended_at=None,
    )
    participants = [
        RoomParticipant(
            room_id=room_id,
            user_id=participant_id,
            role='participant',
            joined_at=datetime.now(timezone.utc),
            left_at=None,
            is_kicked=False,
        ),
        RoomParticipant(
            room_id=room_id,
            user_id=moderator_id,
            role='moderator',
            joined_at=datetime.now(timezone.utc),
            left_at=None,
            is_kicked=False,
        ),
        RoomParticipant(
            room_id=room_id,
            user_id=other_author_id,
            role='participant',
            joined_at=datetime.now(timezone.utc),
            left_at=None,
            is_kicked=False,
        ),
    ]
    message = ChatMessage(
        id=message_id,
        room_id=room_id,
        sender_id=other_author_id,
        content='message',
        is_edited=False,
    )
    element = BoardElement(
        id=element_id,
        room_id=room_id,
        author_id=other_author_id,
        element_type=BoardElementType.TEXT,
        data={'text': 'note'},
        is_anonymous=False,
        is_deleted=False,
    )
    comment = BoardElementComment(
        id=comment_id,
        board_element_id=element_id,
        author_id=other_author_id,
        content='comment',
        is_anonymous=False,
        is_deleted=False,
    )

    service = RoomAccessService(
        room_repository=InMemoryRepository([room]),
        room_participant_repository=InMemoryRepository(participants),
        chat_message_repository=InMemoryRepository([message]),
        board_element_repository=InMemoryRepository([element]),
        board_element_comment_repository=InMemoryRepository([comment]),
    )

    assert await service.get_actor_role(room_id, owner_id) == 'owner'
    assert await service.get_actor_role(room_id, participant_id) == 'participant'
    assert await service.get_actor_role(room_id, moderator_id) == 'moderator'

    await service.ensure_can_moderate(room_id, owner_id)
    await service.ensure_can_moderate(room_id, moderator_id)
    with pytest.raises(HTTPException) as moderate_error:
        await service.ensure_can_moderate(room_id, participant_id)
    assert moderate_error.value.status_code == status.HTTP_403_FORBIDDEN

    await service.ensure_message_manage(room_id, message_id, owner_id)
    await service.ensure_message_manage(room_id, message_id, moderator_id)
    await service.ensure_message_manage(room_id, message_id, other_author_id)
    with pytest.raises(HTTPException) as message_error:
        await service.ensure_message_manage(room_id, message_id, participant_id)
    assert message_error.value.status_code == status.HTTP_403_FORBIDDEN

    await service.ensure_board_element_manage(room_id, element_id, owner_id)
    await service.ensure_board_element_manage(room_id, element_id, moderator_id)
    with pytest.raises(HTTPException) as element_error:
        await service.ensure_board_element_manage(room_id, element_id, participant_id)
    assert element_error.value.status_code == status.HTTP_403_FORBIDDEN

    await service.ensure_comment_manage(room_id, element_id, comment_id, owner_id)
    await service.ensure_comment_manage(room_id, element_id, comment_id, moderator_id)
    with pytest.raises(HTTPException) as comment_error:
        await service.ensure_comment_manage(
            room_id,
            element_id,
            comment_id,
            participant_id,
        )
    assert comment_error.value.status_code == status.HTTP_403_FORBIDDEN

    with pytest.raises(HTTPException) as missing_message_error:
        await service.ensure_message_manage(room_id, uuid4(), owner_id)
    assert missing_message_error.value.status_code == status.HTTP_404_NOT_FOUND

    room.status = RoomStatus.ENDED
    with pytest.raises(HTTPException) as ended_error:
        await service.get_actor_role(room_id, owner_id)
    assert ended_error.value.status_code == status.HTTP_409_CONFLICT
