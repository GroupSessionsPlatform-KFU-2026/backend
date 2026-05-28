from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from socketio.exceptions import ConnectionRefusedError as SocketConnectionRefusedError
from src.app.models.permission import Permission
from src.app.models.role import Role
from src.app.models.room import Room, RoomStatus
from src.app.models.room_participant import RoomParticipant
from src.app.models.user import User
from src.app.sockets import auth as socket_auth
from src.app.sockets import server
from src.app.sockets.auth import SocketAuthContext
from src.app.sockets.events import common, presence
from src.app.sockets.events.contexts import SocketServiceFactory
from src.app.sockets.manager import ConnectedClient, SocketConnectionManager

EXPECTED_CONNECTIONS = 2


class SocketTestError(Exception):
    pass


class FakeSocketServer:
    def __init__(self) -> None:
        self.sessions: dict[str, dict] = {}
        self.entered_rooms: list[tuple[str, str]] = []
        self.left_rooms: list[tuple[str, str]] = []
        self.emitted: list[dict] = []
        self.disconnected: list[str] = []
        self.handlers: dict[str, object] = {}

    async def save_session(self, sid: str, data: dict) -> None:
        self.sessions[sid] = data

    async def get_session(self, sid: str) -> dict:
        return self.sessions.get(sid, {})

    async def enter_room(self, sid: str, room: str) -> None:
        self.entered_rooms.append((sid, room))

    async def leave_room(self, sid: str, room: str) -> None:
        self.left_rooms.append((sid, room))

    async def emit(self, **kwargs) -> None:
        self.emitted.append(kwargs)

    async def disconnect(self, sid: str) -> None:
        self.disconnected.append(sid)

    def on(self, event_name: str):
        def decorator(callback):
            self.handlers[event_name] = callback
            return callback

        return decorator


def install_socket_auth_fakes(
    monkeypatch,
    *,
    users_by_token: dict[str, User],
    room_repository,
    participant_repository,
) -> None:
    @asynccontextmanager
    async def fake_session_maker():
        yield object()

    class FakeAuthService:
        def __init__(self, **kwargs) -> None:
            _ = kwargs

        async def get_current_user(self, token: str, required_scopes: list[str]):
            assert required_scopes == ['rooms:read']
            if token not in users_by_token:
                raise SocketTestError('bad token')
            return users_by_token[token]

    class FakeRepository:
        def __class_getitem__(cls, model):
            def build(_session):
                if model is Room:
                    return room_repository
                if model.__name__ == 'RoomParticipant':
                    return participant_repository
                return object()

            return build

    monkeypatch.setattr(socket_auth, 'async_session_maker', fake_session_maker)
    monkeypatch.setattr(socket_auth, 'AuthService', FakeAuthService)
    monkeypatch.setattr(socket_auth, 'Repository', FakeRepository)

    def build_user_repository(_session):
        return object()

    def build_user_service(*, user_repository):
        _ = user_repository
        return object()

    def build_email_service(*, background_tasks):
        _ = background_tasks
        return object()

    monkeypatch.setattr(socket_auth, 'UserRepository', build_user_repository)
    monkeypatch.setattr(socket_auth, 'UserService', build_user_service)
    monkeypatch.setattr(socket_auth, 'EmailService', build_email_service)


async def test_socket_connection_manager_tracks_presence_and_emits():
    fake_sio = FakeSocketServer()
    manager = SocketConnectionManager(fake_sio)
    room_id = uuid4()
    user_id = uuid4()

    client = await manager.register_connection('sid-1')
    assert client.sid == 'sid-1'

    attached = await manager.attach_identity(
        sid='sid-1',
        user_id=user_id,
        room_id=room_id,
        role='owner',
    )
    await manager.attach_identity(
        sid='sid-2',
        user_id=user_id,
        room_id=room_id,
        role='owner',
    )

    assert manager.get_client('sid-1') == attached
    assert (
        manager.count_user_connections_in_room(room_id, user_id) == EXPECTED_CONNECTIONS
    )
    assert len(manager.list_clients_in_room(room_id)) == EXPECTED_CONNECTIONS
    assert len(manager.list_unique_users_in_room(room_id)) == 1

    snapshot = manager.build_presence_snapshot(room_id)
    assert snapshot['count'] == 1
    assert snapshot['participants'][0]['user_id'] == str(user_id)

    await manager.save_socket_session('sid-1', {'user_id': str(user_id)})
    assert await manager.get_socket_session('sid-1') == {'user_id': str(user_id)}

    await manager.join_room('sid-1', room_id)
    await manager.emit_to_room(room_id, 'event.name', {'ok': True}, skip_sid='sid-1')
    await manager.emit_to_client('sid-1', 'client.event', {'ok': True})
    await manager.force_disconnect('sid-1')
    disconnected = await manager.disconnect('sid-1')

    assert disconnected == attached
    assert fake_sio.entered_rooms == [('sid-1', f'room:{room_id}')]
    assert fake_sio.left_rooms == [('sid-1', f'room:{room_id}')]
    assert fake_sio.disconnected == ['sid-1']
    assert fake_sio.emitted[0]['event'] == 'event.name'
    assert fake_sio.emitted[1]['to'] == 'sid-1'


async def test_socket_common_validation_and_registration_helpers():
    fake_sio = FakeSocketServer()
    manager = SocketConnectionManager(fake_sio)
    room_id = uuid4()
    user_id = uuid4()
    identity = common.SocketIdentity(
        user_id=user_id,
        room_id=room_id,
        role='participant',
        scopes=['rooms:read', 'board:write'],
    )

    assert common.error_response('bad') == {'ok': False, 'error': 'bad'}
    assert common.ok_response(value=1) == {'ok': True, 'value': 1}
    assert common.require_payload_dict({'a': 1}, SocketTestError) == {'a': 1}
    assert common.parse_uuid(str(room_id), 'room id', SocketTestError) == room_id
    assert (
        common.require_non_empty_string('  hello  ', 'name', SocketTestError) == 'hello'
    )

    with pytest.raises(SocketTestError, match='Invalid payload'):
        common.require_payload_dict(None, SocketTestError)
    with pytest.raises(SocketTestError, match='Invalid room id'):
        common.parse_uuid('not-a-uuid', 'room id', SocketTestError)
    with pytest.raises(SocketTestError, match='must be a string'):
        common.require_non_empty_string(42, 'name', SocketTestError)
    with pytest.raises(SocketTestError, match='cannot be empty'):
        common.require_non_empty_string(' ', 'name', SocketTestError)
    with pytest.raises(SocketTestError, match='Not enough permissions'):
        common.require_scope(identity, 'board:delete', SocketTestError)
    with pytest.raises(SocketTestError, match='Only owners'):
        common.ensure_role(identity, {'owner'}, 'Only owners', SocketTestError)
    with pytest.raises(SocketTestError, match='Cannot edit'):
        common.ensure_can_manage_resource(
            author_id=uuid4(),
            identity=identity,
            message='Cannot edit',
            error_cls=SocketTestError,
        )

    await manager.save_socket_session(
        'sid-1',
        {
            'user_id': str(user_id),
            'room_id': str(room_id),
            'role': 'participant',
            'scopes': ['rooms:read', 123],
        },
    )
    restored_identity = await common.require_identity(manager, 'sid-1', SocketTestError)
    assert restored_identity.scopes == ['rooms:read']

    await manager.save_socket_session('sid-2', {'user_id': 'broken'})
    assert await common.get_socket_identity(manager, 'sid-2') is None
    with pytest.raises(SocketTestError, match='not authenticated'):
        await common.require_identity(manager, 'missing', SocketTestError)

    async def handler(_, __, ___):
        return common.ok_response(done=True)

    async def failing_handler(_, __, ___):
        raise SocketTestError('boom')

    common.register_event_handlers(
        fake_sio,
        manager,
        {
            'ok.event': handler,
            'fail.event': failing_handler,
        },
        SocketTestError,
    )
    assert await fake_sio.handlers['ok.event']('sid-1', {}) == {
        'ok': True,
        'done': True,
    }
    assert await fake_sio.handlers['fail.event']('sid-1', {}) == {
        'ok': False,
        'error': 'boom',
    }


async def test_socket_room_active_and_presence_helpers():
    fake_sio = FakeSocketServer()
    manager = SocketConnectionManager(fake_sio)
    room_id = uuid4()
    user_id = uuid4()
    client = ConnectedClient(
        sid='sid-1',
        user_id=user_id,
        room_id=room_id,
        role='moderator',
    )
    await manager.attach_identity('sid-1', user_id, room_id, 'moderator')

    class RoomRepository:
        def __init__(self, room: Room | None) -> None:
            self.room = room

        async def get(self, requested_room_id):
            assert requested_room_id == room_id
            return self.room

    active_room = Room(
        id=room_id,
        title='Room',
        room_code='ABC123',
        max_participants=4,
        project_id=uuid4(),
        creator_id=user_id,
        status=RoomStatus.ACTIVE,
    )
    ended_room = active_room.model_copy(update={'status': RoomStatus.ENDED})

    assert (
        await common.ensure_room_is_active(
            RoomRepository(active_room),
            room_id,
            SocketTestError,
        )
    ) == active_room
    with pytest.raises(SocketTestError, match='Room not found'):
        await common.ensure_room_is_active(
            RoomRepository(None),
            room_id,
            SocketTestError,
        )
    with pytest.raises(SocketTestError, match='Room already ended'):
        await common.ensure_room_is_active(
            RoomRepository(ended_room),
            room_id,
            SocketTestError,
        )

    await presence.emit_presence_snapshot_to_room(manager, room_id)
    await presence.emit_participant_joined(manager, client, skip_sid='sid-1')
    await presence.emit_participant_left(manager, client)
    await presence.emit_room_ended_and_disconnect(manager, room_id)
    await presence.emit_participant_joined(manager, ConnectedClient(sid='missing'))
    await presence.emit_participant_left(manager, ConnectedClient(sid='missing'))

    emitted_events = [event['event'] for event in fake_sio.emitted]
    assert emitted_events == [
        'room.presence.snapshot',
        'participant.joined',
        'participant.left',
        'room.ended',
    ]
    assert fake_sio.disconnected == ['sid-1']


def test_socket_auth_extractors_and_scope_collection():
    room_id = uuid4()
    permission = Permission(subject='rooms', action='read')
    role = Role(name='public')
    role.permissions = [permission]
    user = User(
        email='socket@example.com',
        username='socket-user',
        avatar_url=None,
        password_hash='hash',
        is_active=True,
        is_verified=True,
    )
    user.roles = [role]

    assert socket_auth._extract_access_token({'access_token': ' token '}) == ' token '
    assert socket_auth._extract_room_id({'room_id': str(room_id)}) == room_id
    assert socket_auth._collect_user_scopes(user) == ['rooms:read']

    invalid_auth_values = [None, {}, {'access_token': ''}]
    for auth_value in invalid_auth_values:
        with pytest.raises(SocketConnectionRefusedError):
            socket_auth._extract_access_token(auth_value)

    with pytest.raises(SocketConnectionRefusedError, match='Missing room id'):
        socket_auth._extract_room_id({})
    with pytest.raises(SocketConnectionRefusedError, match='Invalid room id'):
        socket_auth._extract_room_id({'room_id': 'broken'})


async def test_socket_auth_connection_accepts_owner_and_participant(monkeypatch):
    room_id = uuid4()
    owner_id = uuid4()
    participant_id = uuid4()
    permission = Permission(subject='rooms', action='read')
    role = Role(name='public')
    role.permissions = [permission]
    owner = User(
        id=owner_id,
        email='socket-owner@example.com',
        username='socket-owner',
        avatar_url=None,
        password_hash='hash',
        is_active=True,
        is_verified=True,
    )
    owner.roles = [role]
    participant = owner.model_copy(
        update={
            'id': participant_id,
            'email': 'socket-participant@example.com',
            'username': 'socket-participant',
        }
    )
    participant.roles = [role]
    room = Room(
        id=room_id,
        title='Socket auth room',
        max_participants=5,
        project_id=uuid4(),
        creator_id=owner_id,
        room_code='ABC123',
        status=RoomStatus.ACTIVE,
        ended_at=None,
    )

    class RoomRepository:
        async def get(self, requested_room_id):
            assert requested_room_id == room_id
            return room

    class ParticipantRepository:
        async def fetch(self, extra_filters):
            if extra_filters['user_id'] == participant_id:
                return [
                    RoomParticipant(
                        room_id=room_id,
                        user_id=participant_id,
                        role='moderator',
                        joined_at=None,
                        left_at=None,
                        is_kicked=False,
                    )
                ]
            return []

    install_socket_auth_fakes(
        monkeypatch,
        users_by_token={
            'owner-token': owner,
            'participant-token': participant,
        },
        room_repository=RoomRepository(),
        participant_repository=ParticipantRepository(),
    )

    owner_context = await socket_auth.authenticate_socket_connection(
        {
            'access_token': 'owner-token',
            'room_id': str(room_id),
        }
    )
    participant_context = await socket_auth.authenticate_socket_connection(
        {
            'access_token': 'participant-token',
            'room_id': str(room_id),
        }
    )

    assert owner_context.role == 'owner'
    assert owner_context.scopes == ['rooms:read']
    assert participant_context.role == 'moderator'


async def test_socket_auth_connection_rejects_invalid_room_states(monkeypatch):
    room_id = uuid4()
    user = User(
        email='socket-denied@example.com',
        username='socket-denied',
        avatar_url=None,
        password_hash='hash',
        is_active=True,
        is_verified=True,
    )
    user.roles = []

    class RoomRepository:
        def __init__(self, room: Room | None) -> None:
            self.room = room

        async def get(self, requested_room_id):
            assert requested_room_id == room_id
            return self.room

    class EmptyParticipantRepository:
        async def fetch(self, extra_filters):
            _ = extra_filters
            return []

    ended_room = Room(
        id=room_id,
        title='Ended socket auth room',
        max_participants=5,
        project_id=uuid4(),
        creator_id=uuid4(),
        room_code='ABC123',
        status=RoomStatus.ENDED,
        ended_at=None,
    )
    active_room = ended_room.model_copy(update={'status': RoomStatus.ACTIVE})

    socket_auth_cases = {
        'Invalid access token': {
            'tokens': {},
            'room_repository': RoomRepository(active_room),
        },
        'Room not found': {
            'tokens': {'token': user},
            'room_repository': RoomRepository(None),
        },
        'Room already ended': {
            'tokens': {'token': user},
            'room_repository': RoomRepository(ended_room),
        },
        'User has no access to this room': {
            'tokens': {'token': user},
            'room_repository': RoomRepository(active_room),
        },
    }

    for expected_message, case in socket_auth_cases.items():
        install_socket_auth_fakes(
            monkeypatch,
            users_by_token=case['tokens'],
            room_repository=case['room_repository'],
            participant_repository=EmptyParticipantRepository(),
        )

        with pytest.raises(SocketConnectionRefusedError, match=expected_message):
            await socket_auth.authenticate_socket_connection(
                {
                    'access_token': 'token',
                    'room_id': str(room_id),
                }
            )


async def test_socket_server_connect_and_disconnect(monkeypatch):
    room_id = uuid4()
    user_id = uuid4()
    events: list[tuple[str, object]] = []

    class FakeServerManager:
        def __init__(self) -> None:
            self.count_calls = 0
            self.client = ConnectedClient(
                sid='sid-1',
                user_id=user_id,
                room_id=room_id,
                role='owner',
            )

        async def register_connection(self, sid: str) -> None:
            events.append(('register', sid))

        async def attach_identity(self, sid: str, user_id, room_id, role):
            events.append(('attach', (sid, user_id, room_id, role)))
            return self.client

        async def save_socket_session(self, sid: str, data: dict) -> None:
            events.append(('save', (sid, data)))

        async def join_room(self, sid: str, room_id) -> None:
            events.append(('join', (sid, room_id)))

        def count_user_connections_in_room(self, room_id, user_id) -> int:
            events.append(('count', (room_id, user_id)))
            self.count_calls += 1
            return 1 if self.count_calls == 1 else 0

        def get_client(self, sid: str):
            events.append(('get', sid))
            return self.client

        async def disconnect(self, sid: str):
            events.append(('disconnect', sid))
            return self.client

    async def authenticate(_auth):
        return SocketAuthContext(
            user_id=user_id,
            room_id=room_id,
            role='owner',
            scopes=['rooms:read'],
        )

    async def emit_joined(**kwargs):
        events.append(('joined', kwargs['client'].sid))

    async def emit_left(**kwargs):
        events.append(('left', kwargs['client'].sid))

    async def emit_presence(**kwargs):
        events.append(('presence', kwargs['room_id']))

    fake_manager = FakeServerManager()
    monkeypatch.setattr(server, 'socket_manager', fake_manager)
    monkeypatch.setattr(server, 'authenticate_socket_connection', authenticate)
    monkeypatch.setattr(server, 'emit_participant_joined', emit_joined)
    monkeypatch.setattr(server, 'emit_participant_left', emit_left)
    monkeypatch.setattr(server, 'emit_presence_snapshot_to_room', emit_presence)

    assert await server.connect('sid-1', {}, {'access_token': 'token'}) is True
    await server.disconnect('sid-1', 'client disconnect')

    assert ('joined', 'sid-1') in events
    assert ('left', 'sid-1') in events
    assert ('presence', room_id) in events


async def test_socket_server_rejects_failed_auth(monkeypatch):
    events: list[tuple[str, str]] = []

    class FakeServerManager:
        async def register_connection(self, sid: str) -> None:
            events.append(('register', sid))

        async def disconnect(self, sid: str):
            events.append(('disconnect', sid))

    async def authenticate(_auth):
        raise SocketConnectionRefusedError('bad auth')

    monkeypatch.setattr(server, 'socket_manager', FakeServerManager())
    monkeypatch.setattr(server, 'authenticate_socket_connection', authenticate)

    with pytest.raises(SocketConnectionRefusedError):
        await server.connect('sid-2', {}, {'access_token': 'bad'})

    assert events == [('register', 'sid-2'), ('disconnect', 'sid-2')]


async def test_socket_context_factory_builds_services(monkeypatch):
    class FakeSessionMaker:
        @asynccontextmanager
        async def __call__(self):
            yield object()

    monkeypatch.setattr(
        'src.app.sockets.events.contexts.async_session_maker',
        FakeSessionMaker(),
    )

    factory = SocketServiceFactory()
    async with factory.chat() as (_, chat_service):
        assert chat_service is not None
    async with factory.board() as (_, board_service):
        assert board_service is not None
    async with factory.board_comments() as (_, comment_service):
        assert comment_service is not None
    async with factory.pomodoro() as (_, pomodoro_service):
        assert pomodoro_service is not None
