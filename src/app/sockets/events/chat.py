from uuid import UUID

import socketio

from src.app.models.chat_message import ChatMessageCreate, ChatMessageUpdate
from src.app.sockets.events.common import (
    ensure_can_manage_resource,
    ensure_room_is_active,
    ok_response,
    parse_uuid,
    register_event_handlers,
    require_identity,
    require_non_empty_string,
    require_payload_dict,
    require_scope,
)
from src.app.sockets.events.contexts import chat_context
from src.app.sockets.manager import SocketConnectionManager


class ChatEventError(Exception):
    pass


def _extract_content(payload: dict) -> str:
    return require_non_empty_string(payload.get('content'), 'content', ChatEventError)


def _extract_message_id(payload: dict) -> UUID:
    return parse_uuid(payload.get('message_id'), 'message id', ChatEventError)


async def _handle_chat_send(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, object]:
    payload = require_payload_dict(data, ChatEventError)
    content = _extract_content(payload)

    identity = await require_identity(socket_manager, sid, ChatEventError)
    require_scope(identity, 'chat:write', ChatEventError)

    async with chat_context() as (room_repository, chat_service):
        await ensure_room_is_active(room_repository, identity.room_id, ChatEventError)

        created_message = await chat_service.create_message(
            room_id=identity.room_id,
            message_create=ChatMessageCreate(
                room_id=identity.room_id,
                sender_id=identity.user_id,
                content=content,
            ),
        )

    message_payload = created_message.model_dump(mode='json')

    await socket_manager.emit_to_room(
        room_id=identity.room_id,
        event='chat.message.created',
        data=message_payload,
    )

    return ok_response(message=message_payload)


async def _handle_chat_update(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, object]:
    payload = require_payload_dict(data, ChatEventError)
    message_id = _extract_message_id(payload)
    content = _extract_content(payload)

    identity = await require_identity(socket_manager, sid, ChatEventError)
    require_scope(identity, 'chat:write', ChatEventError)

    async with chat_context() as (room_repository, chat_service):
        await ensure_room_is_active(room_repository, identity.room_id, ChatEventError)

        existing_message = await chat_service.get_message_in_room(
            room_id=identity.room_id,
            message_id=message_id,
        )
        if existing_message is None:
            raise ChatEventError('Message not found')

        ensure_can_manage_resource(
            author_id=existing_message.sender_id,
            identity=identity,
            message='You cannot edit this message',
            error_cls=ChatEventError,
        )

        updated_message = await chat_service.update_message(
            room_id=identity.room_id,
            message_id=message_id,
            message_update=ChatMessageUpdate(content=content),
        )
        if updated_message is None:
            raise ChatEventError('Message not found')

    message_payload = updated_message.model_dump(mode='json')

    await socket_manager.emit_to_room(
        room_id=identity.room_id,
        event='chat.message.updated',
        data=message_payload,
    )

    return ok_response(message=message_payload)


async def _handle_chat_delete(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, object]:
    payload = require_payload_dict(data, ChatEventError)
    message_id = _extract_message_id(payload)

    identity = await require_identity(socket_manager, sid, ChatEventError)
    require_scope(identity, 'chat:delete', ChatEventError)

    async with chat_context() as (room_repository, chat_service):
        await ensure_room_is_active(room_repository, identity.room_id, ChatEventError)

        existing_message = await chat_service.get_message_in_room(
            room_id=identity.room_id,
            message_id=message_id,
        )
        if existing_message is None:
            raise ChatEventError('Message not found')

        ensure_can_manage_resource(
            author_id=existing_message.sender_id,
            identity=identity,
            message='You cannot delete this message',
            error_cls=ChatEventError,
        )

        deleted_message = await chat_service.delete_message(
            room_id=identity.room_id,
            message_id=message_id,
        )
        if deleted_message is None:
            raise ChatEventError('Message not found')

    deleted_payload = {
        'id': str(message_id),
        'room_id': str(identity.room_id),
    }

    await socket_manager.emit_to_room(
        room_id=identity.room_id,
        event='chat.message.deleted',
        data=deleted_payload,
    )

    return ok_response(deleted_message_id=str(message_id))


def register_chat_events(
    sio: socketio.AsyncServer,
    socket_manager: SocketConnectionManager,
) -> None:
    register_event_handlers(
        sio=sio,
        socket_manager=socket_manager,
        handlers={
            'chat.send': _handle_chat_send,
            'chat.update': _handle_chat_update,
            'chat.delete': _handle_chat_delete,
        },
        error_cls=ChatEventError,
    )
