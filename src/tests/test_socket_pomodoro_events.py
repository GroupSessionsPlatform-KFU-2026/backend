from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from src.app.models.pomodoro_session import PomodoroPhase, PomodoroSession
from src.app.models.room import Room, RoomStatus
from src.app.sockets.events import pomodoro
from src.app.sockets.manager import SocketConnectionManager

UPDATED_WORK_DURATION = 30


class FakeSocketServer:
    def __init__(self) -> None:
        self.sessions: dict[str, dict] = {}
        self.handlers: dict[str, object] = {}
        self.emitted: list[dict] = []

    def on(self, event_name: str):
        def decorator(callback):
            self.handlers[event_name] = callback
            return callback

        return decorator

    async def save_session(self, sid: str, data: dict) -> None:
        self.sessions[sid] = data

    async def get_session(self, sid: str) -> dict:
        return self.sessions.get(sid, {})

    async def emit(self, **kwargs) -> None:
        self.emitted.append(kwargs)


class FakeRoomRepository:
    def __init__(self, room: Room | None) -> None:
        self.room = room

    async def get(self, _room_id):
        return self.room


class FakePomodoroService:
    def __init__(self, session: PomodoroSession | None) -> None:
        self.session = session

    async def get_room_pomodoro(self, _room_id):
        return self.session

    async def update_room_pomodoro(self, room_id, pomodoro_update):
        _ = room_id
        if self.session is None:
            return None

        for key, value in pomodoro_update.model_dump(exclude_unset=True).items():
            setattr(self.session, key, value)
        return self.session

    async def start_pomodoro(self, _room_id):
        if self.session is None:
            return None

        self.session.is_running = True
        return self.session

    async def pause_pomodoro(self, _room_id):
        if self.session is None:
            return None

        self.session.is_running = False
        return self.session

    async def reset_pomodoro(self, _room_id):
        if self.session is None:
            return None

        self.session.current_phase = PomodoroPhase.WORK
        self.session.completed_cycles = 0
        self.session.is_running = False
        return self.session


async def test_pomodoro_socket_events_handle_full_timer_flow(monkeypatch):
    fake_sio = FakeSocketServer()
    manager = SocketConnectionManager(fake_sio)
    room_id = uuid4()
    user_id = uuid4()
    room = Room(
        id=room_id,
        title='Socket pomodoro room',
        max_participants=5,
        project_id=uuid4(),
        creator_id=user_id,
        room_code='ABC123',
        status=RoomStatus.ACTIVE,
        ended_at=None,
    )
    session = PomodoroSession(
        room_id=room_id,
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
    service = FakePomodoroService(session)

    @asynccontextmanager
    async def pomodoro_context():
        yield FakeRoomRepository(room), service

    monkeypatch.setattr(
        pomodoro.socket_service_factory,
        'pomodoro',
        pomodoro_context,
    )
    await manager.save_socket_session(
        'sid-1',
        {
            'user_id': str(user_id),
            'room_id': str(room_id),
            'role': 'owner',
            'scopes': ['pomodoro:read', 'pomodoro:write'],
        },
    )

    handler = pomodoro.PomodoroSocketEventHandler(manager)
    handler.register(fake_sio)

    state_response = await fake_sio.handlers['pomodoro.state.get']('sid-1')
    assert state_response['ok'] is True
    assert state_response['state']['room_id'] == str(room_id)

    settings_response = await fake_sio.handlers['pomodoro.settings.update'](
        'sid-1',
        {
            'work_duration': UPDATED_WORK_DURATION,
            'short_break_duration': 10,
            'long_break_duration': 20,
            'cycles_before_long': 3,
        },
    )
    assert settings_response['ok'] is True
    assert settings_response['state']['work_duration'] == UPDATED_WORK_DURATION

    start_response = await fake_sio.handlers['pomodoro.start']('sid-1')
    assert start_response['ok'] is True
    assert start_response['state']['is_running'] is True

    pause_response = await fake_sio.handlers['pomodoro.pause']('sid-1')
    assert pause_response['ok'] is True
    assert pause_response['state']['is_running'] is False

    session.current_phase = PomodoroPhase.LONG_BREAK
    session.completed_cycles = 2
    reset_response = await fake_sio.handlers['pomodoro.reset']('sid-1')
    assert reset_response['ok'] is True
    assert reset_response['state']['current_phase'] == PomodoroPhase.WORK
    assert reset_response['state']['completed_cycles'] == 0

    emitted_events = [event['event'] for event in fake_sio.emitted]
    assert emitted_events == [
        'pomodoro.state.updated',
        'pomodoro.state.updated',
        'pomodoro.state.updated',
        'pomodoro.state.updated',
    ]


async def test_pomodoro_socket_events_return_errors_for_invalid_payloads(
    monkeypatch,
):
    fake_sio = FakeSocketServer()
    manager = SocketConnectionManager(fake_sio)
    room_id = uuid4()
    user_id = uuid4()
    room = Room(
        id=room_id,
        title='Socket pomodoro room',
        max_participants=5,
        project_id=uuid4(),
        creator_id=user_id,
        room_code='ABC123',
        status=RoomStatus.ACTIVE,
        ended_at=None,
    )
    session = PomodoroSession(
        room_id=room_id,
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

    @asynccontextmanager
    async def pomodoro_context():
        yield FakeRoomRepository(room), FakePomodoroService(session)

    monkeypatch.setattr(
        pomodoro.socket_service_factory,
        'pomodoro',
        pomodoro_context,
    )
    await manager.save_socket_session(
        'sid-1',
        {
            'user_id': str(user_id),
            'room_id': str(room_id),
            'role': 'participant',
            'scopes': ['pomodoro:read', 'pomodoro:write'],
        },
    )

    handler = pomodoro.PomodoroSocketEventHandler(manager)
    handler.register(fake_sio)

    invalid_payload_response = await fake_sio.handlers['pomodoro.settings.update'](
        'sid-1',
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
