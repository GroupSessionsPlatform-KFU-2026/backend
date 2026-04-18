from typing import Any
from uuid import UUID

import socketio
from pydantic import ValidationError

from src.app.models.board_element import BoardElementCreate, BoardElementUpdate
from src.app.schemas.board_elements_filters import BoardElementType
from src.app.sockets.events.common import (
    ensure_can_manage_resource,
    ensure_room_is_active,
    ok_response,
    parse_uuid,
    register_event_handlers,
    require_identity,
    require_payload_dict,
    require_scope,
)
from src.app.sockets.events.contexts import board_context
from src.app.sockets.manager import SocketConnectionManager


class BoardSocketError(Exception):
    pass


def _require_data_object(raw_data: Any) -> dict[str, Any]:
    if not isinstance(raw_data, dict):
        raise BoardSocketError('Field "data" must be an object')
    return raw_data


def _build_create_payload(
    payload: dict[str, Any],
    room_id: UUID,
    author_id: UUID,
) -> BoardElementCreate:
    try:
        return BoardElementCreate(
            room_id=room_id,
            author_id=author_id,
            element_type=BoardElementType(payload.get('element_type')),
            data=_require_data_object(payload.get('data')),
        )
    except (ValidationError, ValueError, TypeError) as error:
        raise BoardSocketError(f'Invalid board payload: {error}') from error


def _build_update_payload(payload: dict[str, Any]) -> tuple[UUID, BoardElementUpdate]:
    element_id = parse_uuid(payload.get('element_id'), 'element id', BoardSocketError)

    try:
        element_update = BoardElementUpdate(
            element_type=BoardElementType(payload.get('element_type')),
            data=_require_data_object(payload.get('data')),
        )
    except (ValidationError, ValueError, TypeError) as error:
        raise BoardSocketError(f'Invalid board payload: {error}') from error

    return element_id, element_update


async def _handle_board_create(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, Any]:
    payload = require_payload_dict(data, BoardSocketError)
    identity = await require_identity(socket_manager, sid, BoardSocketError)
    require_scope(identity, 'board:write', BoardSocketError)

    element_create = _build_create_payload(
        payload=payload,
        room_id=identity.room_id,
        author_id=identity.user_id,
    )

    async with board_context() as (room_repository, board_service):
        await ensure_room_is_active(room_repository, identity.room_id, BoardSocketError)

        created_element = await board_service.create_element(
            room_id=identity.room_id,
            element_create=element_create,
        )

    element_payload = created_element.model_dump(mode='json')

    await socket_manager.emit_to_room(
        room_id=identity.room_id,
        event='board.element.created',
        data=element_payload,
    )

    return ok_response(element=element_payload)


async def _handle_board_update(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, Any]:
    payload = require_payload_dict(data, BoardSocketError)
    identity = await require_identity(socket_manager, sid, BoardSocketError)
    require_scope(identity, 'board:write', BoardSocketError)

    element_id, element_update = _build_update_payload(payload)

    async with board_context() as (room_repository, board_service):
        await ensure_room_is_active(room_repository, identity.room_id, BoardSocketError)

        existing_element = await board_service.get_element_in_room(
            room_id=identity.room_id,
            element_id=element_id,
        )
        if existing_element is None:
            raise BoardSocketError('Element not found')

        ensure_can_manage_resource(
            author_id=existing_element.author_id,
            identity=identity,
            message='You cannot edit this element',
            error_cls=BoardSocketError,
        )

        updated_element = await board_service.update_element(
            room_id=identity.room_id,
            element_id=element_id,
            element_update=element_update,
        )
        if updated_element is None:
            raise BoardSocketError('Element not found')

    element_payload = updated_element.model_dump(mode='json')

    await socket_manager.emit_to_room(
        room_id=identity.room_id,
        event='board.element.updated',
        data=element_payload,
    )

    return ok_response(element=element_payload)


async def _handle_board_delete(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, Any]:
    payload = require_payload_dict(data, BoardSocketError)
    identity = await require_identity(socket_manager, sid, BoardSocketError)
    require_scope(identity, 'board:delete', BoardSocketError)

    element_id = parse_uuid(payload.get('element_id'), 'element id', BoardSocketError)

    async with board_context() as (room_repository, board_service):
        await ensure_room_is_active(room_repository, identity.room_id, BoardSocketError)

        existing_element = await board_service.get_element_in_room(
            room_id=identity.room_id,
            element_id=element_id,
        )
        if existing_element is None:
            raise BoardSocketError('Element not found')

        ensure_can_manage_resource(
            author_id=existing_element.author_id,
            identity=identity,
            message='You cannot delete this element',
            error_cls=BoardSocketError,
        )

        deleted_element = await board_service.delete_element(
            room_id=identity.room_id,
            element_id=element_id,
        )
        if deleted_element is None:
            raise BoardSocketError('Element not found')

    deleted_payload = {
        'id': str(element_id),
        'room_id': str(identity.room_id),
        'is_deleted': True,
    }

    await socket_manager.emit_to_room(
        room_id=identity.room_id,
        event='board.element.deleted',
        data=deleted_payload,
    )

    return ok_response(deleted_element_id=str(element_id))


def register_board_events(
    sio: socketio.AsyncServer,
    socket_manager: SocketConnectionManager,
) -> None:
    register_event_handlers(
        sio=sio,
        socket_manager=socket_manager,
        handlers={
            'board.element.create': _handle_board_create,
            'board.element.update': _handle_board_update,
            'board.element.delete': _handle_board_delete,
        },
        error_cls=BoardSocketError,
    )
