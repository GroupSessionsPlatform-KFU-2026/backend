from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from src.app.models.board_element import BoardElement
from src.app.models.project import Project
from src.app.models.room import Room, RoomStatus
from src.app.models.user import User
from src.app.schemas.board_elements_filters import BoardElementType
from src.app.sockets.events import contexts
from src.app.sockets.events.board import BoardSocketEventHandler
from src.app.sockets.events.board_comments import BoardCommentSocketEventHandler
from src.app.sockets.events.chat import ChatSocketEventHandler
from src.app.sockets.manager import SocketConnectionManager
from src.app.utils.repository import Repository
from src.tests.socket_harness import RecordingSocketServer

pytestmark = pytest.mark.asyncio

SOCKET_SID = 'sid-1'


@dataclass(slots=True)
class SocketTestIdentity:
    user_id: UUID
    room_id: UUID
    role: str
    scopes: list[str]


async def create_socket_identity(
    session_maker,
    scopes: list[str],
    role: str = 'owner',
) -> SocketTestIdentity:
    async with session_maker() as session:
        user_repository = Repository[User](session)
        project_repository = Repository[Project](session)
        room_repository = Repository[Room](session)

        user_id = uuid4().hex
        user = await user_repository.save(
            User(
                email=f'socket-{user_id}@example.com',
                username=f'socket-{user_id}',
                avatar_url=None,
                password_hash='hash',
                is_active=True,
                is_verified=True,
            )
        )
        project = await project_repository.save(
            Project(
                title='Socket project',
                description='Project for socket tests',
                required_roles=[],
                owner_id=user.id,
                is_archived=False,
            )
        )
        room = await room_repository.save(
            Room(
                title='Socket room',
                max_participants=5,
                project_id=project.id,
                creator_id=user.id,
                room_code=f'{uuid4().hex[:6].upper()}',
                status=RoomStatus.ACTIVE,
                ended_at=None,
            )
        )

    return SocketTestIdentity(
        user_id=user.id,
        room_id=room.id,
        role=role,
        scopes=scopes,
    )


async def create_socket_harness(
    identity: SocketTestIdentity,
) -> tuple[RecordingSocketServer, SocketConnectionManager]:
    socket_server = RecordingSocketServer()
    socket_manager = SocketConnectionManager(socket_server)
    await socket_manager.save_socket_session(
        SOCKET_SID,
        {
            'user_id': str(identity.user_id),
            'room_id': str(identity.room_id),
            'role': identity.role,
            'scopes': identity.scopes,
        },
    )
    return socket_server, socket_manager


async def create_board_element(session_maker, identity: SocketTestIdentity):
    async with session_maker() as session:
        board_repository = Repository[BoardElement](session)
        return await board_repository.save(
            BoardElement(
                room_id=identity.room_id,
                author_id=identity.user_id,
                element_type=BoardElementType.TEXT,
                data={'text': 'Existing board note'},
                is_anonymous=False,
                is_deleted=False,
            )
        )


def get_handlers(socket_server: RecordingSocketServer) -> dict[str, object]:
    return socket_server.handlers['/']


async def test_chat_socket_create_update_delete_lifecycle(
    monkeypatch,
    session_maker,
):
    monkeypatch.setattr(contexts, 'async_session_maker', session_maker)
    identity = await create_socket_identity(
        session_maker,
        ['chat:write', 'chat:delete'],
    )
    socket_server, socket_manager = await create_socket_harness(identity)
    ChatSocketEventHandler(socket_manager).register(socket_server)
    handlers = get_handlers(socket_server)

    create_response = await handlers['chat.send'](
        SOCKET_SID,
        {'content': 'Hello socket'},
    )
    message_id = create_response['message']['id']

    assert create_response['ok'] is True
    assert create_response['message']['content'] == 'Hello socket'
    assert socket_server.emitted[0]['event'] == 'chat.message.created'

    update_response = await handlers['chat.update'](
        SOCKET_SID,
        {
            'message_id': message_id,
            'content': 'Updated socket message',
        },
    )
    assert update_response['ok'] is True
    assert update_response['message']['is_edited'] is True
    assert socket_server.emitted[1]['event'] == 'chat.message.updated'

    delete_response = await handlers['chat.delete'](
        SOCKET_SID,
        {'message_id': message_id},
    )
    assert delete_response == {
        'ok': True,
        'deleted_message_id': message_id,
    }
    assert socket_server.emitted[2]['event'] == 'chat.message.deleted'


async def test_chat_socket_rejects_invalid_payload_and_missing_scope(
    session_maker,
):
    identity = await create_socket_identity(session_maker, ['chat:write'])
    socket_server, socket_manager = await create_socket_harness(identity)
    ChatSocketEventHandler(socket_manager).register(socket_server)
    handlers = get_handlers(socket_server)

    invalid_response = await handlers['chat.send'](SOCKET_SID, None)
    assert invalid_response == {'ok': False, 'error': 'Invalid payload'}

    no_scope_response = await handlers['chat.delete'](
        SOCKET_SID,
        {'message_id': str(uuid4())},
    )
    assert no_scope_response == {'ok': False, 'error': 'Not enough permissions'}


async def test_board_socket_create_update_delete_and_clear(
    monkeypatch,
    session_maker,
):
    monkeypatch.setattr(contexts, 'async_session_maker', session_maker)
    identity = await create_socket_identity(
        session_maker,
        ['board:write', 'board:delete'],
    )
    socket_server, socket_manager = await create_socket_harness(identity)
    BoardSocketEventHandler(socket_manager).register(socket_server)
    handlers = get_handlers(socket_server)

    create_response = await handlers['board.element.create'](
        SOCKET_SID,
        {
            'element_type': BoardElementType.TEXT,
            'data': {'text': 'Board note'},
            'is_anonymous': True,
        },
    )
    element_id = create_response['element']['id']

    assert create_response['ok'] is True
    assert create_response['element']['author_id'] is None

    update_response = await handlers['board.element.update'](
        SOCKET_SID,
        {
            'element_id': element_id,
            'element_type': BoardElementType.QUESTION,
            'data': {'text': 'Question'},
            'is_anonymous': False,
        },
    )
    assert update_response['ok'] is True
    assert update_response['element']['element_type'] == BoardElementType.QUESTION

    delete_response = await handlers['board.element.delete'](
        SOCKET_SID,
        {'element_id': element_id},
    )
    assert delete_response == {
        'ok': True,
        'deleted_element_id': element_id,
    }

    second_create_response = await handlers['board.element.create'](
        SOCKET_SID,
        {
            'element_type': BoardElementType.TEXT,
            'data': {'text': 'Board note for clear'},
            'is_anonymous': False,
        },
    )
    assert second_create_response['ok'] is True

    clear_response = await handlers['board.clear'](SOCKET_SID)
    assert clear_response == {
        'ok': True,
        'room_id': str(identity.room_id),
        'deleted_count': 1,
    }
    assert [event['event'] for event in socket_server.emitted] == [
        'board.element.created',
        'board.element.updated',
        'board.element.deleted',
        'board.element.created',
        'board.cleared',
    ]


async def test_board_socket_rejects_invalid_data_and_forbidden_clear(
    monkeypatch,
    session_maker,
):
    monkeypatch.setattr(contexts, 'async_session_maker', session_maker)
    identity = await create_socket_identity(
        session_maker,
        ['board:write', 'board:delete'],
        role='participant',
    )
    socket_server, socket_manager = await create_socket_harness(identity)
    BoardSocketEventHandler(socket_manager).register(socket_server)
    handlers = get_handlers(socket_server)

    invalid_response = await handlers['board.element.create'](
        SOCKET_SID,
        {
            'element_type': BoardElementType.TEXT,
            'data': ['not object'],
        },
    )
    assert invalid_response == {
        'ok': False,
        'error': 'Field "data" must be an object',
    }

    clear_response = await handlers['board.clear'](SOCKET_SID)
    assert clear_response == {
        'ok': False,
        'error': 'Only owner or moderator can clear board',
    }


async def test_board_comment_socket_create_update_delete(
    monkeypatch,
    session_maker,
):
    monkeypatch.setattr(contexts, 'async_session_maker', session_maker)
    identity = await create_socket_identity(
        session_maker,
        ['board:write', 'board:delete'],
    )
    element = await create_board_element(session_maker, identity)
    socket_server, socket_manager = await create_socket_harness(identity)
    BoardCommentSocketEventHandler(socket_manager).register(socket_server)
    handlers = get_handlers(socket_server)

    create_response = await handlers['board.comment.create'](
        SOCKET_SID,
        {
            'element_id': str(element.id),
            'content': 'Comment',
            'is_anonymous': True,
        },
    )
    comment_id = create_response['comment']['id']

    assert create_response['ok'] is True
    assert create_response['comment']['author_id'] is None

    update_response = await handlers['board.comment.update'](
        SOCKET_SID,
        {
            'element_id': str(element.id),
            'comment_id': comment_id,
            'content': 'Updated comment',
            'is_anonymous': False,
        },
    )
    assert update_response['ok'] is True
    assert update_response['comment']['content'] == 'Updated comment'

    delete_response = await handlers['board.comment.delete'](
        SOCKET_SID,
        {
            'element_id': str(element.id),
            'comment_id': comment_id,
        },
    )
    assert delete_response == {
        'ok': True,
        'deleted_comment_id': comment_id,
    }
    assert [event['event'] for event in socket_server.emitted] == [
        'board.comment.created',
        'board.comment.updated',
        'board.comment.deleted',
    ]
