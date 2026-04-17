from uuid import UUID

import socketio

from src.app.dependencies.session import async_session_maker
from src.app.models.chat_message import (
    ChatMessage,
    ChatMessageCreate,
    ChatMessageUpdate,
)
from src.app.models.room import Room, RoomStatus
from src.app.services.chat_messages import ChatMessageService
from src.app.sockets.manager import SocketConnectionManager
from src.app.utils.repository import Repository


class ChatEventError(Exception):
    pass


def _error_response(message: str) -> dict[str, object]:
    return {
        'ok': False,
        'error': message,
    }


async def _get_socket_identity(
    socket_manager: SocketConnectionManager,
    sid: str,
) -> tuple[UUID, UUID, str, list[str]] | None:
    session_data = await socket_manager.get_socket_session(sid)

    raw_user_id = session_data.get('user_id')
    raw_room_id = session_data.get('room_id')
    role = session_data.get('role')
    scopes = session_data.get('scopes', [])

    if not raw_user_id or not raw_room_id or not isinstance(role, str):
        return None

    if not isinstance(scopes, list):
        scopes = []

    try:
        user_id = UUID(str(raw_user_id))
        room_id = UUID(str(raw_room_id))
    except ValueError:
        return None

    safe_scopes = [scope for scope in scopes if isinstance(scope, str)]
    return user_id, room_id, role, safe_scopes


def _has_scope(scopes: list[str], required_scope: str) -> bool:
    return required_scope in scopes


def _extract_content(data: dict | None) -> str:
    if not isinstance(data, dict):
        raise ChatEventError('Invalid payload')

    raw_content = data.get('content')
    if not isinstance(raw_content, str):
        raise ChatEventError('Content must be a string')

    content = raw_content.strip()
    if not content:
        raise ChatEventError('Content cannot be empty')

    return content


def _extract_message_id(data: dict | None) -> UUID:
    if not isinstance(data, dict):
        raise ChatEventError('Invalid payload')

    raw_message_id = data.get('message_id')

    try:
        return UUID(str(raw_message_id))
    except ValueError as error:
        raise ChatEventError('Invalid message id') from error


async def _require_identity(
    socket_manager: SocketConnectionManager,
    sid: str,
) -> tuple[UUID, UUID, str, list[str]]:
    identity = await _get_socket_identity(socket_manager, sid)
    if identity is None:
        raise ChatEventError('Socket session is not authenticated')
    return identity


def _require_scope(scopes: list[str], required_scope: str) -> None:
    if not _has_scope(scopes, required_scope):
        raise ChatEventError('Not enough permissions')


async def _get_active_room(
    room_repository: Repository[Room],
    room_id: UUID,
) -> Room:
    room = await room_repository.get(room_id)
    if room is None:
        raise ChatEventError('Room not found')

    if room.status == RoomStatus.ENDED:
        raise ChatEventError('Room already ended')

    return room


def _ensure_can_edit_message(
    sender_id: UUID,
    user_id: UUID,
    role: str,
) -> None:
    can_edit = sender_id == user_id or role in {'owner', 'moderator'}
    if not can_edit:
        raise ChatEventError('You cannot edit this message')


def _ensure_can_delete_message(
    sender_id: UUID,
    user_id: UUID,
    role: str,
) -> None:
    can_delete = sender_id == user_id or role in {'owner', 'moderator'}
    if not can_delete:
        raise ChatEventError('You cannot delete this message')


async def _handle_chat_send(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, object]:
    content = _extract_content(data)
    user_id, room_id, _role, scopes = await _require_identity(socket_manager, sid)
    _require_scope(scopes, 'chat:write')

    async with async_session_maker() as db_session:
        room_repository = Repository[Room](db_session)
        chat_repository = Repository[ChatMessage](db_session)
        chat_service = ChatMessageService(repository=chat_repository)

        await _get_active_room(room_repository, room_id)

        message_create = ChatMessageCreate(
            room_id=room_id,
            sender_id=user_id,
            content=content,
        )

        created_message = await chat_service.create_message(
            room_id=room_id,
            message_create=message_create,
        )

    payload = created_message.model_dump(mode='json')

    await socket_manager.emit_to_room(
        room_id=room_id,
        event='chat.message.created',
        data=payload,
    )

    return {
        'ok': True,
        'message': payload,
    }


async def _handle_chat_update(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, object]:
    message_id = _extract_message_id(data)
    content = _extract_content(data)
    user_id, room_id, role, scopes = await _require_identity(socket_manager, sid)
    _require_scope(scopes, 'chat:write')

    async with async_session_maker() as db_session:
        room_repository = Repository[Room](db_session)
        chat_repository = Repository[ChatMessage](db_session)
        chat_service = ChatMessageService(repository=chat_repository)

        await _get_active_room(room_repository, room_id)

        existing_message = await chat_service.get_message_in_room(
            room_id=room_id,
            message_id=message_id,
        )
        if existing_message is None:
            raise ChatEventError('Message not found')

        _ensure_can_edit_message(existing_message.sender_id, user_id, role)

        updated_message = await chat_service.update_message(
            room_id=room_id,
            message_id=message_id,
            message_update=ChatMessageUpdate(content=content),
        )

    if updated_message is None:
        raise ChatEventError('Message not found')

    payload = updated_message.model_dump(mode='json')

    await socket_manager.emit_to_room(
        room_id=room_id,
        event='chat.message.updated',
        data=payload,
    )

    return {
        'ok': True,
        'message': payload,
    }


async def _handle_chat_delete(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, object]:
    message_id = _extract_message_id(data)
    user_id, room_id, role, scopes = await _require_identity(socket_manager, sid)
    _require_scope(scopes, 'chat:delete')

    async with async_session_maker() as db_session:
        room_repository = Repository[Room](db_session)
        chat_repository = Repository[ChatMessage](db_session)
        chat_service = ChatMessageService(repository=chat_repository)

        await _get_active_room(room_repository, room_id)

        existing_message = await chat_service.get_message_in_room(
            room_id=room_id,
            message_id=message_id,
        )
        if existing_message is None:
            raise ChatEventError('Message not found')

        _ensure_can_delete_message(existing_message.sender_id, user_id, role)

        deleted_message = await chat_service.delete_message(
            room_id=room_id,
            message_id=message_id,
        )

    if deleted_message is None:
        raise ChatEventError('Message not found')

    payload = {
        'id': str(message_id),
        'room_id': str(room_id),
    }

    await socket_manager.emit_to_room(
        room_id=room_id,
        event='chat.message.deleted',
        data=payload,
    )

    return {
        'ok': True,
        'deleted_message_id': str(message_id),
    }


def register_chat_events(
    sio: socketio.AsyncServer,
    socket_manager: SocketConnectionManager,
) -> None:
    @sio.on('chat.send')
    async def handle_chat_send_event(sid: str, data: dict | None):
        try:
            return await _handle_chat_send(socket_manager, sid, data)
        except ChatEventError as error:
            return _error_response(str(error))

    @sio.on('chat.update')
    async def handle_chat_update_event(sid: str, data: dict | None):
        try:
            return await _handle_chat_update(socket_manager, sid, data)
        except ChatEventError as error:
            return _error_response(str(error))

    @sio.on('chat.delete')
    async def handle_chat_delete_event(sid: str, data: dict | None):
        try:
            return await _handle_chat_delete(socket_manager, sid, data)
        except ChatEventError as error:
            return _error_response(str(error))
