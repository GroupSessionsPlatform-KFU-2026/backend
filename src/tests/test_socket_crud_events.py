from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from src.app.models.board_element import BoardElement, BoardElementPublic
from src.app.models.board_element_comment import (
    BoardElementComment,
    BoardElementCommentPublic,
)
from src.app.models.chat_message import ChatMessage, ChatMessageWithSender
from src.app.models.room import Room, RoomStatus
from src.app.schemas.board_elements_filters import BoardElementType
from src.app.sockets.events import board, board_comments, chat
from src.app.sockets.events.board import BoardSocketEventHandler
from src.app.sockets.events.board_comments import BoardCommentSocketEventHandler
from src.app.sockets.events.chat import ChatSocketEventHandler

pytestmark = pytest.mark.asyncio


@dataclass(slots=True)
class SocketTestIdentity:
    user_id: UUID
    room_id: UUID
    role: str
    scopes: list[str]


class FakeSocketServer:
    def __init__(self) -> None:
        self.handlers: dict[str, object] = {}

    def on(self, event_name: str):
        def decorator(callback):
            self.handlers[event_name] = callback
            return callback

        return decorator


class FakeSocketManager:
    def __init__(self, identity: SocketTestIdentity) -> None:
        self.identity = identity
        self.emitted: list[dict] = []

    async def get_socket_session(self, sid: str) -> dict:
        if sid != 'sid-1':
            return {}

        return {
            'user_id': str(self.identity.user_id),
            'room_id': str(self.identity.room_id),
            'role': self.identity.role,
            'scopes': self.identity.scopes,
        }

    async def emit_to_room(
        self,
        *,
        room_id: UUID,
        event: str,
        data: dict,
        skip_sid: str | None = None,
    ) -> None:
        self.emitted.append(
            {
                'room_id': room_id,
                'event': event,
                'data': data,
                'skip_sid': skip_sid,
            }
        )


class ActiveRoomRepository:
    def __init__(self, identity: SocketTestIdentity) -> None:
        self.identity = identity

    async def get(self, room_id: UUID) -> Room:
        return Room(
            id=room_id,
            title='Socket room',
            max_participants=5,
            project_id=uuid4(),
            creator_id=self.identity.user_id,
            room_code='ABC123',
            status=RoomStatus.ACTIVE,
            ended_at=None,
        )


class FakeChatService:
    def __init__(self, identity: SocketTestIdentity) -> None:
        self.identity = identity
        self.message: ChatMessage | None = None

    async def create_message(self, room_id: UUID, message_create) -> ChatMessage:
        self.message = ChatMessage(
            room_id=room_id,
            sender_id=message_create.sender_id,
            content=message_create.content,
            is_edited=False,
        )
        return self.message

    async def get_message_in_room(
        self,
        room_id: UUID,
        message_id: UUID,
    ) -> ChatMessage | None:
        if (
            self.message
            and self.message.room_id == room_id
            and self.message.id == message_id
        ):
            return self.message
        return None

    async def update_message(self, room_id: UUID, message_id: UUID, message_update):
        message = await self.get_message_in_room(room_id, message_id)
        if message is None:
            return None

        message.content = message_update.content
        message.is_edited = True
        return message

    async def delete_message(self, room_id: UUID, message_id: UUID):
        return await self.get_message_in_room(room_id, message_id)

    async def to_public(self, message: ChatMessage) -> ChatMessageWithSender:
        return ChatMessageWithSender(
            **message.model_dump(),
            sender_username='socket-user',
        )


class FakeBoardService:
    def __init__(self, identity: SocketTestIdentity) -> None:
        self.identity = identity
        self.element: BoardElement | None = None

    async def create_element(self, room_id: UUID, element_create) -> BoardElement:
        self.element = BoardElement(
            room_id=room_id,
            author_id=element_create.author_id,
            element_type=element_create.element_type,
            data=element_create.data,
            is_anonymous=element_create.is_anonymous,
            is_deleted=False,
        )
        return self.element

    async def get_element_in_room(
        self,
        room_id: UUID,
        element_id: UUID,
    ) -> BoardElement | None:
        if (
            self.element
            and self.element.room_id == room_id
            and self.element.id == element_id
        ):
            return self.element
        return None

    async def update_element(self, room_id: UUID, element_id: UUID, element_update):
        element = await self.get_element_in_room(room_id, element_id)
        if element is None:
            return None

        element.element_type = element_update.element_type
        element.data = element_update.data
        element.is_anonymous = element_update.is_anonymous
        return element

    async def delete_element(self, room_id: UUID, element_id: UUID):
        element = await self.get_element_in_room(room_id, element_id)
        if element is not None:
            element.is_deleted = True
        return element

    async def clear_room_elements(self, room_id: UUID) -> int:
        if self.element and self.element.room_id == room_id:
            self.element.is_deleted = True
            return 1
        return 0

    def to_public(self, element: BoardElement) -> BoardElementPublic:
        return BoardElementPublic(
            **element.model_dump(exclude={'author_id'}),
            author_id=None if element.is_anonymous else element.author_id,
        )


class FakeBoardCommentService:
    def __init__(self, identity: SocketTestIdentity) -> None:
        self.identity = identity
        self.comment: BoardElementComment | None = None

    async def create_comment(
        self,
        room_id: UUID,
        element_id: UUID,
        comment_create,
    ) -> BoardElementComment:
        assert room_id == self.identity.room_id
        self.comment = BoardElementComment(
            board_element_id=element_id,
            author_id=comment_create.author_id,
            content=comment_create.content,
            is_anonymous=comment_create.is_anonymous,
            is_deleted=False,
        )
        return self.comment

    async def get_comment_in_element(
        self,
        room_id: UUID,
        element_id: UUID,
        comment_id: UUID,
    ) -> BoardElementComment | None:
        assert room_id == self.identity.room_id
        if (
            self.comment
            and self.comment.board_element_id == element_id
            and self.comment.id == comment_id
        ):
            return self.comment
        return None

    async def update_comment(
        self,
        room_id: UUID,
        element_id: UUID,
        comment_id: UUID,
        comment_update,
    ):
        comment = await self.get_comment_in_element(room_id, element_id, comment_id)
        if comment is None:
            return None

        comment.content = comment_update.content
        comment.is_anonymous = comment_update.is_anonymous
        return comment

    async def delete_comment(
        self,
        room_id: UUID,
        element_id: UUID,
        comment_id: UUID,
    ):
        comment = await self.get_comment_in_element(room_id, element_id, comment_id)
        if comment is not None:
            comment.is_deleted = True
        return comment

    def to_public(self, comment: BoardElementComment) -> BoardElementCommentPublic:
        return BoardElementCommentPublic(
            **comment.model_dump(exclude={'author_id'}),
            author_id=None if comment.is_anonymous else comment.author_id,
        )


def build_identity(scopes: list[str], role: str = 'owner') -> SocketTestIdentity:
    return SocketTestIdentity(
        user_id=uuid4(),
        room_id=uuid4(),
        role=role,
        scopes=scopes,
    )


async def test_chat_socket_create_update_delete_lifecycle(monkeypatch):
    identity = build_identity(['chat:write', 'chat:delete'])
    socket_manager = FakeSocketManager(identity)
    chat_service = FakeChatService(identity)

    @asynccontextmanager
    async def chat_context() -> AsyncIterator[
        tuple[ActiveRoomRepository, FakeChatService]
    ]:
        yield ActiveRoomRepository(identity), chat_service

    monkeypatch.setattr(chat.socket_service_factory, 'chat', chat_context)

    socket_server = FakeSocketServer()
    ChatSocketEventHandler(socket_manager).register(socket_server)

    create_response = await socket_server.handlers['chat.send'](
        'sid-1',
        {'content': 'Hello socket'},
    )
    message_id = create_response['message']['id']

    assert create_response['ok'] is True
    assert create_response['message']['content'] == 'Hello socket'
    assert socket_manager.emitted[0]['event'] == 'chat.message.created'

    update_response = await socket_server.handlers['chat.update'](
        'sid-1',
        {
            'message_id': message_id,
            'content': 'Updated socket message',
        },
    )
    assert update_response['ok'] is True
    assert update_response['message']['is_edited'] is True
    assert socket_manager.emitted[1]['event'] == 'chat.message.updated'

    delete_response = await socket_server.handlers['chat.delete'](
        'sid-1',
        {'message_id': message_id},
    )
    assert delete_response == {
        'ok': True,
        'deleted_message_id': message_id,
    }
    assert socket_manager.emitted[2]['event'] == 'chat.message.deleted'


async def test_chat_socket_rejects_invalid_payload_and_missing_scope(monkeypatch):
    identity = build_identity(['chat:write'])
    socket_manager = FakeSocketManager(identity)

    @asynccontextmanager
    async def chat_context() -> AsyncIterator[
        tuple[ActiveRoomRepository, FakeChatService]
    ]:
        yield ActiveRoomRepository(identity), FakeChatService(identity)

    monkeypatch.setattr(chat.socket_service_factory, 'chat', chat_context)

    socket_server = FakeSocketServer()
    ChatSocketEventHandler(socket_manager).register(socket_server)

    invalid_response = await socket_server.handlers['chat.send']('sid-1', None)
    assert invalid_response == {'ok': False, 'error': 'Invalid payload'}

    no_scope_response = await socket_server.handlers['chat.delete'](
        'sid-1',
        {'message_id': str(uuid4())},
    )
    assert no_scope_response == {'ok': False, 'error': 'Not enough permissions'}


async def test_board_socket_create_update_delete_and_clear(monkeypatch):
    identity = build_identity(['board:write', 'board:delete'])
    socket_manager = FakeSocketManager(identity)
    board_service = FakeBoardService(identity)

    @asynccontextmanager
    async def board_context() -> AsyncIterator[
        tuple[ActiveRoomRepository, FakeBoardService]
    ]:
        yield ActiveRoomRepository(identity), board_service

    monkeypatch.setattr(board.socket_service_factory, 'board', board_context)

    socket_server = FakeSocketServer()
    BoardSocketEventHandler(socket_manager).register(socket_server)

    create_response = await socket_server.handlers['board.element.create'](
        'sid-1',
        {
            'element_type': BoardElementType.TEXT,
            'data': {'text': 'Board note'},
            'is_anonymous': True,
        },
    )
    element_id = create_response['element']['id']

    assert create_response['ok'] is True
    assert create_response['element']['author_id'] is None

    update_response = await socket_server.handlers['board.element.update'](
        'sid-1',
        {
            'element_id': element_id,
            'element_type': BoardElementType.QUESTION,
            'data': {'text': 'Question'},
            'is_anonymous': False,
        },
    )
    assert update_response['ok'] is True
    assert update_response['element']['element_type'] == BoardElementType.QUESTION

    delete_response = await socket_server.handlers['board.element.delete'](
        'sid-1',
        {'element_id': element_id},
    )
    assert delete_response == {
        'ok': True,
        'deleted_element_id': element_id,
    }

    clear_response = await socket_server.handlers['board.clear']('sid-1')
    assert clear_response == {
        'ok': True,
        'room_id': str(identity.room_id),
        'deleted_count': 1,
    }
    assert [event['event'] for event in socket_manager.emitted] == [
        'board.element.created',
        'board.element.updated',
        'board.element.deleted',
        'board.cleared',
    ]


async def test_board_socket_rejects_invalid_data_and_forbidden_clear(monkeypatch):
    identity = build_identity(['board:write', 'board:delete'], role='participant')
    socket_manager = FakeSocketManager(identity)

    @asynccontextmanager
    async def board_context() -> AsyncIterator[
        tuple[ActiveRoomRepository, FakeBoardService]
    ]:
        yield ActiveRoomRepository(identity), FakeBoardService(identity)

    monkeypatch.setattr(board.socket_service_factory, 'board', board_context)

    socket_server = FakeSocketServer()
    BoardSocketEventHandler(socket_manager).register(socket_server)

    invalid_response = await socket_server.handlers['board.element.create'](
        'sid-1',
        {
            'element_type': BoardElementType.TEXT,
            'data': ['not object'],
        },
    )
    assert invalid_response == {
        'ok': False,
        'error': 'Field "data" must be an object',
    }

    clear_response = await socket_server.handlers['board.clear']('sid-1')
    assert clear_response == {
        'ok': False,
        'error': 'Only owner or moderator can clear board',
    }


async def test_board_comment_socket_create_update_delete(monkeypatch):
    identity = build_identity(['board:write', 'board:delete'])
    element_id = uuid4()
    socket_manager = FakeSocketManager(identity)
    comment_service = FakeBoardCommentService(identity)

    @asynccontextmanager
    async def comment_context() -> AsyncIterator[
        tuple[ActiveRoomRepository, FakeBoardCommentService]
    ]:
        yield ActiveRoomRepository(identity), comment_service

    monkeypatch.setattr(
        board_comments.socket_service_factory,
        'board_comments',
        comment_context,
    )

    socket_server = FakeSocketServer()
    BoardCommentSocketEventHandler(socket_manager).register(socket_server)

    create_response = await socket_server.handlers['board.comment.create'](
        'sid-1',
        {
            'element_id': str(element_id),
            'content': 'Comment',
            'is_anonymous': True,
        },
    )
    comment_id = create_response['comment']['id']

    assert create_response['ok'] is True
    assert create_response['comment']['author_id'] is None

    update_response = await socket_server.handlers['board.comment.update'](
        'sid-1',
        {
            'element_id': str(element_id),
            'comment_id': comment_id,
            'content': 'Updated comment',
            'is_anonymous': False,
        },
    )
    assert update_response['ok'] is True
    assert update_response['comment']['content'] == 'Updated comment'

    delete_response = await socket_server.handlers['board.comment.delete'](
        'sid-1',
        {
            'element_id': str(element_id),
            'comment_id': comment_id,
        },
    )
    assert delete_response == {
        'ok': True,
        'deleted_comment_id': comment_id,
    }
    assert [event['event'] for event in socket_manager.emitted] == [
        'board.comment.created',
        'board.comment.updated',
        'board.comment.deleted',
    ]
