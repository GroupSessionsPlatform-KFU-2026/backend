from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from src.app.models.board_element import BoardElement
from src.app.models.board_element_comment import BoardElementComment
from src.app.models.chat_message import ChatMessage
from src.app.models.pomodoro_session import (
    PomodoroPhase,
    PomodoroSession,
    PomodoroSessionCreate,
    PomodoroSessionUpdate,
)
from src.app.models.project import Project
from src.app.models.room import Room, RoomStatus
from src.app.models.room_participant import RoomParticipant
from src.app.models.user import User, UserCreate, UserUpdate
from src.app.schemas.board_elements_filters import BoardElementType
from src.app.schemas.pomodoro_session_filters import PomodoroSessionFilter
from src.app.schemas.user_filters import UserFilters
from src.app.services.pomodoro_sessions import PomodoroSessionService
from src.app.services.room_access import RoomAccessService
from src.app.services.users import UserService
from src.app.utils.repository import Repository
from src.app.utils.user_repository import UserRepository

UPDATED_WORK_DURATION = 30


async def create_service_user(user_repository: Repository[User], label: str) -> User:
    user_id = uuid4().hex
    return await user_repository.save(
        User(
            email=f'{label}-{user_id}@example.com',
            username=f'{label}-{user_id}',
            avatar_url=None,
            password_hash='hash',
            is_active=True,
            is_verified=True,
        )
    )


async def test_user_service_hashes_password_and_crud_uses_repository(session_maker):
    async with session_maker() as session:
        service = UserService(UserRepository(session))

        created_user = await service.create_user(
            UserCreate(
                email=f'user-service-{uuid4().hex}@example.com',
                username=f'user-service-{uuid4().hex}',
                avatar_url=None,
                password='test-password-123',
            )
        )

        assert created_user.is_active is True
        assert created_user.password_hash != 'test-password-123'
        assert service.verify_user_password(
            'test-password-123',
            created_user.password_hash,
        )
        assert not service.verify_user_password(
            'bad-password',
            created_user.password_hash,
        )

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


async def test_pomodoro_service_lifecycle_and_missing_session_errors(session_maker):
    room_id = uuid4()
    async with session_maker() as session:
        repository = Repository[PomodoroSession](session)
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


async def test_room_access_service_roles_and_resource_ownership(session_maker):
    async with session_maker() as session:
        user_repository = Repository[User](session)
        project_repository = Repository[Project](session)
        room_repository = Repository[Room](session)
        room_participant_repository = Repository[RoomParticipant](session)
        chat_message_repository = Repository[ChatMessage](session)
        board_element_repository = Repository[BoardElement](session)
        board_element_comment_repository = Repository[BoardElementComment](session)

        owner = await create_service_user(user_repository, 'owner')
        participant = await create_service_user(user_repository, 'participant')
        moderator = await create_service_user(user_repository, 'moderator')
        other_author = await create_service_user(user_repository, 'other-author')
        project = await project_repository.save(
            Project(
                title='Access project',
                description='Project for room access tests',
                required_roles=[],
                owner_id=owner.id,
                is_archived=False,
            )
        )
        room = await room_repository.save(
            Room(
                title='Access room',
                max_participants=5,
                project_id=project.id,
                creator_id=owner.id,
                room_code='ABC123',
                status=RoomStatus.ACTIVE,
                ended_at=None,
            )
        )
        participants = [
            RoomParticipant(
                room_id=room.id,
                user_id=participant.id,
                role='participant',
                joined_at=datetime.now(timezone.utc),
                left_at=None,
                is_kicked=False,
            ),
            RoomParticipant(
                room_id=room.id,
                user_id=moderator.id,
                role='moderator',
                joined_at=datetime.now(timezone.utc),
                left_at=None,
                is_kicked=False,
            ),
            RoomParticipant(
                room_id=room.id,
                user_id=other_author.id,
                role='participant',
                joined_at=datetime.now(timezone.utc),
                left_at=None,
                is_kicked=False,
            ),
        ]
        await room_participant_repository.save_all(participants)
        message = await chat_message_repository.save(
            ChatMessage(
                room_id=room.id,
                sender_id=other_author.id,
                content='message',
                is_edited=False,
            )
        )
        element = await board_element_repository.save(
            BoardElement(
                room_id=room.id,
                author_id=other_author.id,
                element_type=BoardElementType.TEXT,
                data={'text': 'note'},
                is_anonymous=False,
                is_deleted=False,
            )
        )
        comment = await board_element_comment_repository.save(
            BoardElementComment(
                board_element_id=element.id,
                author_id=other_author.id,
                content='comment',
                is_anonymous=False,
                is_deleted=False,
            )
        )

        service = RoomAccessService(
            room_repository=room_repository,
            room_participant_repository=room_participant_repository,
            chat_message_repository=chat_message_repository,
            board_element_repository=board_element_repository,
            board_element_comment_repository=board_element_comment_repository,
        )

        assert await service.get_actor_role(room.id, owner.id) == 'owner'
        assert await service.get_actor_role(room.id, participant.id) == 'participant'
        assert await service.get_actor_role(room.id, moderator.id) == 'moderator'

        await service.ensure_can_moderate(room.id, owner.id)
        await service.ensure_can_moderate(room.id, moderator.id)
        with pytest.raises(HTTPException) as moderate_error:
            await service.ensure_can_moderate(room.id, participant.id)
        assert moderate_error.value.status_code == status.HTTP_403_FORBIDDEN

        await service.ensure_message_manage(room.id, message.id, owner.id)
        await service.ensure_message_manage(room.id, message.id, moderator.id)
        await service.ensure_message_manage(room.id, message.id, other_author.id)
        with pytest.raises(HTTPException) as message_error:
            await service.ensure_message_manage(room.id, message.id, participant.id)
        assert message_error.value.status_code == status.HTTP_403_FORBIDDEN

        await service.ensure_board_element_manage(room.id, element.id, owner.id)
        await service.ensure_board_element_manage(room.id, element.id, moderator.id)
        with pytest.raises(HTTPException) as element_error:
            await service.ensure_board_element_manage(
                room.id,
                element.id,
                participant.id,
            )
        assert element_error.value.status_code == status.HTTP_403_FORBIDDEN

        await service.ensure_comment_manage(room.id, element.id, comment.id, owner.id)
        await service.ensure_comment_manage(
            room.id,
            element.id,
            comment.id,
            moderator.id,
        )
        with pytest.raises(HTTPException) as comment_error:
            await service.ensure_comment_manage(
                room.id,
                element.id,
                comment.id,
                participant.id,
            )
        assert comment_error.value.status_code == status.HTTP_403_FORBIDDEN

        with pytest.raises(HTTPException) as missing_message_error:
            await service.ensure_message_manage(room.id, uuid4(), owner.id)
        assert missing_message_error.value.status_code == status.HTTP_404_NOT_FOUND

        room.status = RoomStatus.ENDED
        await room_repository.save(room)
        with pytest.raises(HTTPException) as ended_error:
            await service.get_actor_role(room.id, owner.id)
        assert ended_error.value.status_code == status.HTTP_409_CONFLICT
