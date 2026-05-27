from uuid import uuid4

import pytest
from src.app.models.pomodoro_session import PomodoroPhase, PomodoroSession
from src.app.models.project import Project
from src.app.models.room import Room, RoomStatus
from src.app.models.user import User
from src.app.sockets.events import contexts, pomodoro
from src.app.sockets.manager import SocketConnectionManager
from src.app.utils.repository import Repository
from src.tests.socket_harness import RecordingSocketServer

UPDATED_WORK_DURATION = 30
SOCKET_SID = 'sid-1'


async def create_pomodoro_socket_state(session_maker):
    async with session_maker() as session:
        user_id = uuid4().hex
        user = await Repository[User](session).save(
            User(
                email=f'pomodoro-socket-{user_id}@example.com',
                username=f'pomodoro-socket-{user_id}',
                avatar_url=None,
                password_hash='hash',
                is_active=True,
                is_verified=True,
            )
        )
        project = await Repository[Project](session).save(
            Project(
                title='Socket pomodoro project',
                description='Project for pomodoro socket tests',
                required_roles=[],
                owner_id=user.id,
                is_archived=False,
            )
        )
        room = await Repository[Room](session).save(
            Room(
                title='Socket pomodoro room',
                max_participants=5,
                project_id=project.id,
                creator_id=user.id,
                room_code=f'{uuid4().hex[:6].upper()}',
                status=RoomStatus.ACTIVE,
                ended_at=None,
            )
        )
        pomodoro_session = await Repository[PomodoroSession](session).save(
            PomodoroSession(
                room_id=room.id,
                work_duration=25,
                short_break_duration=5,
                long_break_duration=15,
                cycles_before_long=4,
                current_phase=PomodoroPhase.WORK,
                completed_cycles=0,
                phase_ends_at=None,
                session_ends_at=None,
                is_running=False,
            )
        )

    return user, room, pomodoro_session


async def create_pomodoro_harness(
    session_maker,
    role: str,
) -> tuple[RecordingSocketServer, SocketConnectionManager, Room, PomodoroSession]:
    user, room, pomodoro_session = await create_pomodoro_socket_state(session_maker)
    socket_server = RecordingSocketServer()
    manager = SocketConnectionManager(socket_server)
    await manager.save_socket_session(
        SOCKET_SID,
        {
            'user_id': str(user.id),
            'room_id': str(room.id),
            'role': role,
            'scopes': ['pomodoro:read', 'pomodoro:write'],
        },
    )
    pomodoro.PomodoroSocketEventHandler(manager).register(socket_server)
    return socket_server, manager, room, pomodoro_session


async def test_pomodoro_socket_events_handle_full_timer_flow(
    monkeypatch,
    session_maker,
):
    monkeypatch.setattr(contexts, 'async_session_maker', session_maker)
    socket_server, _, room, pomodoro_session = await create_pomodoro_harness(
        session_maker,
        role='owner',
    )
    handlers = socket_server.handlers['/']

    state_response = await handlers['pomodoro.state.get'](SOCKET_SID)
    assert state_response['ok'] is True
    assert state_response['state']['room_id'] == str(room.id)

    settings_response = await handlers['pomodoro.settings.update'](
        SOCKET_SID,
        {
            'work_duration': UPDATED_WORK_DURATION,
            'short_break_duration': 10,
            'long_break_duration': 20,
            'cycles_before_long': 3,
        },
    )
    assert settings_response['ok'] is True
    assert settings_response['state']['work_duration'] == UPDATED_WORK_DURATION

    start_response = await handlers['pomodoro.start'](SOCKET_SID)
    assert start_response['ok'] is True
    assert start_response['state']['is_running'] is True

    pause_response = await handlers['pomodoro.pause'](SOCKET_SID)
    assert pause_response['ok'] is True
    assert pause_response['state']['is_running'] is False

    async with session_maker() as session:
        repository = Repository[PomodoroSession](session)
        stored_session = await repository.get(pomodoro_session.id)
        stored_session.current_phase = PomodoroPhase.LONG_BREAK
        stored_session.completed_cycles = 2
        await repository.save(stored_session)

    reset_response = await handlers['pomodoro.reset'](SOCKET_SID)
    assert reset_response['ok'] is True
    assert reset_response['state']['current_phase'] == PomodoroPhase.WORK
    assert reset_response['state']['completed_cycles'] == 0

    emitted_events = [event['event'] for event in socket_server.emitted]
    assert emitted_events == [
        'pomodoro.state.updated',
        'pomodoro.state.updated',
        'pomodoro.state.updated',
        'pomodoro.state.updated',
    ]


async def test_pomodoro_socket_events_return_errors_for_invalid_payloads(
    monkeypatch,
    session_maker,
):
    monkeypatch.setattr(contexts, 'async_session_maker', session_maker)
    socket_server, _, _, _ = await create_pomodoro_harness(
        session_maker,
        role='participant',
    )
    handlers = socket_server.handlers['/']

    invalid_payload_response = await handlers['pomodoro.settings.update'](
        SOCKET_SID,
        {'work_duration': 0},
    )
    assert invalid_payload_response == {
        'ok': False,
        'error': 'Only owner or moderator can control pomodoro',
    }

    with pytest.raises(pomodoro.PomodoroSocketError, match='must be an integer'):
        pomodoro._parse_settings_update(
            {
                'work_duration': 'bad',
                'short_break_duration': 5,
                'long_break_duration': 15,
                'cycles_before_long': 4,
            }
        )

    with pytest.raises(pomodoro.PomodoroSocketError, match='greater than 0'):
        pomodoro._parse_settings_update(
            {
                'work_duration': 0,
                'short_break_duration': 5,
                'long_break_duration': 15,
                'cycles_before_long': 4,
            }
        )
