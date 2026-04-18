from dataclasses import dataclass
from typing import Any, Awaitable, Callable
from uuid import UUID

import socketio

from src.app.models.room import Room, RoomStatus
from src.app.sockets.manager import SocketConnectionManager
from src.app.utils.repository import Repository

type SocketEventHandler = Callable[
    [SocketConnectionManager, str, dict | None],
    Awaitable[dict[str, Any]],
]


@dataclass(slots=True, frozen=True)
class SocketIdentity:
    user_id: UUID
    room_id: UUID
    role: str
    scopes: list[str]


def error_response(message: str) -> dict[str, Any]:
    return {'ok': False, 'error': message}


def ok_response(**extra: Any) -> dict[str, Any]:
    return {'ok': True, **extra}


def require_payload_dict(
    data: dict | None,
    error_cls: type[Exception],
) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise error_cls('Invalid payload')
    return data


def parse_uuid(
    raw_value: Any,
    field_name: str,
    error_cls: type[Exception],
) -> UUID:
    try:
        return UUID(str(raw_value))
    except ValueError as error:
        raise error_cls(f'Invalid {field_name}') from error


def require_non_empty_string(
    raw_value: Any,
    field_name: str,
    error_cls: type[Exception],
) -> str:
    if not isinstance(raw_value, str):
        raise error_cls(f'Field "{field_name}" must be a string')

    value = raw_value.strip()
    if not value:
        raise error_cls(f'Field "{field_name}" cannot be empty')

    return value


async def get_socket_identity(
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


async def require_identity(
    socket_manager: SocketConnectionManager,
    sid: str,
    error_cls: type[Exception],
) -> SocketIdentity:
    identity = await get_socket_identity(socket_manager, sid)
    if identity is None:
        raise error_cls('Socket session is not authenticated')
    return identity


def require_scope(
    identity: SocketIdentity,
    required_scope: str,
    error_cls: type[Exception],
) -> None:
    if required_scope not in identity.scopes:
        raise error_cls('Not enough permissions')


def ensure_role(
    identity: SocketIdentity,
    allowed_roles: set[str],
    message: str,
    error_cls: type[Exception],
) -> None:
    if identity.role not in allowed_roles:
        raise error_cls(message)


def ensure_can_manage_resource(
    author_id: UUID,
    identity: SocketIdentity,
    message: str,
    error_cls: type[Exception],
) -> None:
    can_manage = author_id == identity.user_id or identity.role in {
        'owner',
        'moderator',
    }
    if not can_manage:
        raise error_cls(message)


async def ensure_room_is_active(
    room_repository: Repository[Room],
    room_id: UUID,
    error_cls: type[Exception],
) -> Room:
    room = await room_repository.get(room_id)

    if room is None:
        raise error_cls('Room not found')

    if room.status == RoomStatus.ENDED:
        raise error_cls('Room already ended')

    return room


def register_event_handlers(
    sio: socketio.AsyncServer,
    socket_manager: SocketConnectionManager,
    handlers: dict[str, SocketEventHandler],
    error_cls: type[Exception],
) -> None:
    for event_name, handler in handlers.items():

        async def callback(
            sid: str,
            data: dict | None = None,
            _handler: SocketEventHandler = handler,
        ):
            try:
                return await _handler(socket_manager, sid, data)
            except error_cls as error:
                return error_response(str(error))

        sio.on(event_name)(callback)
