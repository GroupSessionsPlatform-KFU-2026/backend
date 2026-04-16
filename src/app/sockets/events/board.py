from dataclasses import dataclass
from typing import Any
from uuid import UUID

import socketio
from pydantic import ValidationError

from src.app.dependencies.session import async_session_maker
from src.app.models.board_element import (
    BoardElement,
    BoardElementCreate,
    BoardElementUpdate,
)
from src.app.models.room import Room, RoomStatus
from src.app.schemas.board_elements_filters import BoardElementType
from src.app.services.board_elements import BoardElementService
from src.app.sockets.manager import SocketConnectionManager
from src.app.utils.repository import Repository


class BoardSocketError(Exception):
    pass


@dataclass(slots=True, frozen=True)
class SocketIdentity:
    user_id: UUID
    room_id: UUID
    role: str
    scopes: list[str]


async def _get_socket_identity(
    socket_manager: SocketConnectionManager,
    sid: str,
) -> SocketIdentity | None:
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

    return SocketIdentity(
        user_id=user_id,
        room_id=room_id,
        role=role,
        scopes=safe_scopes,
    )


def _error_response(message: str) -> dict[str, Any]:
    return {'ok': False, 'error': message}


def _ok_response(**extra: Any) -> dict[str, Any]:
    return {'ok': True, **extra}


def _has_scope(scopes: list[str], required_scope: str) -> bool:
    return required_scope in scopes


def _require_payload_dict(data: dict | None) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise BoardSocketError('Invalid payload')
    return data


async def _require_identity(
    socket_manager: SocketConnectionManager,
    sid: str,
) -> SocketIdentity:
    identity = await _get_socket_identity(socket_manager, sid)
    if identity is None:
        raise BoardSocketError('Socket session is not authenticated')
    return identity


def _require_scope(identity: SocketIdentity, required_scope: str) -> None:
    if not _has_scope(identity.scopes, required_scope):
        raise BoardSocketError('Not enough permissions')


def _require_element_id(raw_element_id: Any) -> UUID:
    try:
        return UUID(str(raw_element_id))
    except ValueError as error:
        raise BoardSocketError('Invalid element id') from error


def _require_data_object(raw_data: Any) -> dict[str, Any]:
    if not isinstance(raw_data, dict):
        raise BoardSocketError('Field "data" must be an object')
    return raw_data


def _build_create_payload(
    payload: dict[str, Any],
    identity: SocketIdentity,
) -> BoardElementCreate:
    raw_element_type = payload.get('element_type')
    raw_element_data = _require_data_object(payload.get('data'))

    try:
        return BoardElementCreate(
            room_id=identity.room_id,
            author_id=identity.user_id,
            element_type=BoardElementType(raw_element_type),
            data=raw_element_data,
        )
    except (ValidationError, ValueError, TypeError) as error:
        raise BoardSocketError(f'Invalid board payload: {error}') from error


def _build_update_payload(
    payload: dict[str, Any],
) -> tuple[UUID, BoardElementUpdate]:
    element_id = _require_element_id(payload.get('element_id'))
    raw_element_type = payload.get('element_type')
    raw_element_data = _require_data_object(payload.get('data'))

    try:
        element_update = BoardElementUpdate(
            element_type=BoardElementType(raw_element_type),
            data=raw_element_data,
        )
    except (ValidationError, ValueError, TypeError) as error:
        raise BoardSocketError(f'Invalid board payload: {error}') from error

    return element_id, element_update


def _build_delete_payload(payload: dict[str, Any]) -> UUID:
    return _require_element_id(payload.get('element_id'))


def _build_services(
    db_session: Any,
) -> tuple[Repository[Room], BoardElementService]:
    room_repository = Repository[Room](db_session)
    board_repository = Repository[BoardElement](db_session)
    board_service = BoardElementService(repository=board_repository)
    return room_repository, board_service


async def _ensure_room_is_active(
    room_repository: Repository[Room],
    room_id: UUID,
) -> None:
    room = await room_repository.get(room_id)

    if room is None:
        raise BoardSocketError('Room not found')

    if room.status == RoomStatus.ENDED:
        raise BoardSocketError('Room already ended')


async def _require_existing_element(
    board_service: BoardElementService,
    room_id: UUID,
    element_id: UUID,
) -> BoardElement:
    existing_element = await board_service.get_element_in_room(
        room_id=room_id,
        element_id=element_id,
    )

    if existing_element is None:
        raise BoardSocketError('Element not found')

    return existing_element


def _ensure_can_edit(existing_element: BoardElement, user_id: UUID) -> None:
    if existing_element.author_id != user_id:
        raise BoardSocketError('You can edit only your own elements')


def _ensure_can_delete(
    existing_element: BoardElement,
    identity: SocketIdentity,
) -> None:
    can_delete = existing_element.author_id == identity.user_id or identity.role in {
        'owner',
        'moderator',
    }

    if not can_delete:
        raise BoardSocketError('You cannot delete this element')


async def _handle_board_element_create(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, Any]:
    try:
        payload = _require_payload_dict(data)
        identity = await _require_identity(socket_manager, sid)
        _require_scope(identity, 'board:write')
        element_create = _build_create_payload(payload, identity)

        async with async_session_maker() as db_session:
            room_repository, board_service = _build_services(db_session)
            await _ensure_room_is_active(room_repository, identity.room_id)

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
    except BoardSocketError as error:
        return _error_response(str(error))

    return _ok_response(element=element_payload)


async def _handle_board_element_update(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, Any]:
    try:
        payload = _require_payload_dict(data)
        identity = await _require_identity(socket_manager, sid)
        _require_scope(identity, 'board:write')

        element_id, element_update = _build_update_payload(payload)

        async with async_session_maker() as db_session:
            room_repository, board_service = _build_services(db_session)
            await _ensure_room_is_active(room_repository, identity.room_id)

            existing_element = await _require_existing_element(
                board_service=board_service,
                room_id=identity.room_id,
                element_id=element_id,
            )
            _ensure_can_edit(existing_element, identity.user_id)

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
    except BoardSocketError as error:
        return _error_response(str(error))

    return _ok_response(element=element_payload)


async def _handle_board_element_delete(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, Any]:
    try:
        payload = _require_payload_dict(data)
        identity = await _require_identity(socket_manager, sid)
        _require_scope(identity, 'board:delete')

        element_id = _build_delete_payload(payload)

        async with async_session_maker() as db_session:
            room_repository, board_service = _build_services(db_session)
            await _ensure_room_is_active(room_repository, identity.room_id)

            existing_element = await _require_existing_element(
                board_service=board_service,
                room_id=identity.room_id,
                element_id=element_id,
            )
            _ensure_can_delete(existing_element, identity)

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
    except BoardSocketError as error:
        return _error_response(str(error))

    return _ok_response(deleted_element_id=str(element_id))


def register_board_events(
    sio: socketio.AsyncServer,
    socket_manager: SocketConnectionManager,
) -> None:
    @sio.on('board.element.create')
    async def board_element_create(sid: str, data: dict | None):
        return await _handle_board_element_create(socket_manager, sid, data)

    @sio.on('board.element.update')
    async def board_element_update(sid: str, data: dict | None):
        return await _handle_board_element_update(socket_manager, sid, data)

    @sio.on('board.element.delete')
    async def board_element_delete(sid: str, data: dict | None):
        return await _handle_board_element_delete(socket_manager, sid, data)
