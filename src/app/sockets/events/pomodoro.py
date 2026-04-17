from dataclasses import dataclass
from typing import Any
from uuid import UUID

import socketio

from src.app.dependencies.session import async_session_maker
from src.app.models.pomodoro_session import PomodoroSession, PomodoroSessionUpdate
from src.app.models.room import Room, RoomStatus
from src.app.services.pomodoro_sessions import PomodoroSessionService
from src.app.sockets.manager import SocketConnectionManager
from src.app.utils.repository import Repository


class PomodoroSocketError(Exception):
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


async def _require_identity(
    socket_manager: SocketConnectionManager,
    sid: str,
) -> SocketIdentity:
    identity = await _get_socket_identity(socket_manager, sid)
    if identity is None:
        raise PomodoroSocketError('Socket session is not authenticated')
    return identity


def _has_scope(scopes: list[str], required_scope: str) -> bool:
    return required_scope in scopes


def _ensure_scope(scopes: list[str], required_scope: str) -> None:
    if not _has_scope(scopes, required_scope):
        raise PomodoroSocketError(f'Missing required scope: {required_scope}')


def _can_control_pomodoro(role: str) -> bool:
    return role in {'owner', 'moderator'}


def _ensure_can_control(role: str) -> None:
    if not _can_control_pomodoro(role):
        raise PomodoroSocketError('Only owner or moderator can control pomodoro')


def _require_payload_dict(data: dict | None) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise PomodoroSocketError('Invalid payload')
    return data


def _require_positive_int(raw_value: Any, field_name: str) -> int:
    if not isinstance(raw_value, int):
        raise PomodoroSocketError(f'Field "{field_name}" must be an integer')

    if raw_value <= 0:
        raise PomodoroSocketError(f'Field "{field_name}" must be greater than 0')

    return raw_value


def _parse_settings_update(payload: dict[str, Any]) -> PomodoroSessionUpdate:
    return PomodoroSessionUpdate(
        work_duration=_require_positive_int(
            payload.get('work_duration'),
            'work_duration',
        ),
        short_break_duration=_require_positive_int(
            payload.get('short_break_duration'),
            'short_break_duration',
        ),
        long_break_duration=_require_positive_int(
            payload.get('long_break_duration'),
            'long_break_duration',
        ),
        cycles_before_long=_require_positive_int(
            payload.get('cycles_before_long'),
            'cycles_before_long',
        ),
    )


def _build_repositories(
    db_session: Any,
) -> tuple[Repository[Room], Repository[PomodoroSession]]:
    room_repository = Repository[Room](db_session)
    pomodoro_repository = Repository[PomodoroSession](db_session)
    return room_repository, pomodoro_repository


def _build_service(
    pomodoro_repository: Repository[PomodoroSession],
) -> PomodoroSessionService:
    return PomodoroSessionService(repository=pomodoro_repository)


async def _ensure_room_is_active(
    room_repository: Repository[Room],
    room_id: UUID,
) -> None:
    room = await room_repository.get(room_id)

    if room is None:
        raise PomodoroSocketError('Room not found')

    if room.status == RoomStatus.ENDED:
        raise PomodoroSocketError('Room already ended')


async def _load_room_and_service(
    db_session: Any,
) -> tuple[Repository[Room], PomodoroSessionService]:
    room_repository, pomodoro_repository = _build_repositories(db_session)
    pomodoro_service = _build_service(pomodoro_repository)
    return room_repository, pomodoro_service


async def _get_state_payload(
    pomodoro_service: PomodoroSessionService,
    room_id: UUID,
) -> dict[str, Any]:
    pomodoro = await pomodoro_service.get_room_pomodoro(room_id)
    if pomodoro is None:
        raise PomodoroSocketError('Pomodoro session not found')
    return pomodoro.model_dump(mode='json')


async def _emit_state_update(
    socket_manager: SocketConnectionManager,
    room_id: UUID,
    payload: dict[str, Any],
) -> None:
    await socket_manager.emit_to_room(
        room_id=room_id,
        event='pomodoro.state.updated',
        data=payload,
    )


async def _handle_pomodoro_state_get(
    socket_manager: SocketConnectionManager,
    sid: str,
) -> dict[str, Any]:
    try:
        identity = await _require_identity(socket_manager, sid)
        _ensure_scope(identity.scopes, 'pomodoro:read')

        async with async_session_maker() as db_session:
            room_repository, pomodoro_service = await _load_room_and_service(db_session)
            await _ensure_room_is_active(room_repository, identity.room_id)
            state_payload = await _get_state_payload(
                pomodoro_service,
                identity.room_id,
            )
    except PomodoroSocketError as error:
        return _error_response(str(error))

    return _ok_response(state=state_payload)


async def _handle_pomodoro_settings_update(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, Any]:
    try:
        payload = _require_payload_dict(data)
        identity = await _require_identity(socket_manager, sid)
        _ensure_scope(identity.scopes, 'pomodoro:write')
        _ensure_can_control(identity.role)

        pomodoro_update = _parse_settings_update(payload)

        async with async_session_maker() as db_session:
            room_repository, pomodoro_service = await _load_room_and_service(db_session)
            await _ensure_room_is_active(room_repository, identity.room_id)

            updated_pomodoro = await pomodoro_service.update_room_pomodoro(
                room_id=identity.room_id,
                pomodoro_update=pomodoro_update,
            )
            if updated_pomodoro is None:
                raise PomodoroSocketError('Pomodoro session not found')

        state_payload = updated_pomodoro.model_dump(mode='json')
        await _emit_state_update(
            socket_manager=socket_manager,
            room_id=identity.room_id,
            payload=state_payload,
        )
    except PomodoroSocketError as error:
        return _error_response(str(error))

    return _ok_response(state=state_payload)


async def _handle_pomodoro_start(
    socket_manager: SocketConnectionManager,
    sid: str,
) -> dict[str, Any]:
    try:
        identity = await _require_identity(socket_manager, sid)
        _ensure_scope(identity.scopes, 'pomodoro:write')
        _ensure_can_control(identity.role)

        async with async_session_maker() as db_session:
            room_repository, pomodoro_service = await _load_room_and_service(db_session)
            await _ensure_room_is_active(room_repository, identity.room_id)

            started_pomodoro = await pomodoro_service.start_pomodoro(
                room_id=identity.room_id,
            )
            if started_pomodoro is None:
                raise PomodoroSocketError('Pomodoro session not found')

        state_payload = started_pomodoro.model_dump(mode='json')
        await _emit_state_update(
            socket_manager=socket_manager,
            room_id=identity.room_id,
            payload=state_payload,
        )
    except PomodoroSocketError as error:
        return _error_response(str(error))

    return _ok_response(state=state_payload)


async def _handle_pomodoro_pause(
    socket_manager: SocketConnectionManager,
    sid: str,
) -> dict[str, Any]:
    try:
        identity = await _require_identity(socket_manager, sid)
        _ensure_scope(identity.scopes, 'pomodoro:write')
        _ensure_can_control(identity.role)

        async with async_session_maker() as db_session:
            room_repository, pomodoro_service = await _load_room_and_service(db_session)
            await _ensure_room_is_active(room_repository, identity.room_id)

            paused_pomodoro = await pomodoro_service.pause_pomodoro(
                room_id=identity.room_id,
            )
            if paused_pomodoro is None:
                raise PomodoroSocketError('Pomodoro session not found')

        state_payload = paused_pomodoro.model_dump(mode='json')
        await _emit_state_update(
            socket_manager=socket_manager,
            room_id=identity.room_id,
            payload=state_payload,
        )
    except PomodoroSocketError as error:
        return _error_response(str(error))

    return _ok_response(state=state_payload)


async def _handle_pomodoro_reset(
    socket_manager: SocketConnectionManager,
    sid: str,
) -> dict[str, Any]:
    try:
        identity = await _require_identity(socket_manager, sid)
        _ensure_scope(identity.scopes, 'pomodoro:write')
        _ensure_can_control(identity.role)

        async with async_session_maker() as db_session:
            room_repository, pomodoro_service = await _load_room_and_service(db_session)
            await _ensure_room_is_active(room_repository, identity.room_id)

            reset_pomodoro = await pomodoro_service.reset_pomodoro(
                room_id=identity.room_id,
            )
            if reset_pomodoro is None:
                raise PomodoroSocketError('Pomodoro session not found')

        state_payload = reset_pomodoro.model_dump(mode='json')
        await _emit_state_update(
            socket_manager=socket_manager,
            room_id=identity.room_id,
            payload=state_payload,
        )
    except PomodoroSocketError as error:
        return _error_response(str(error))

    return _ok_response(state=state_payload)


def register_pomodoro_events(
    sio: socketio.AsyncServer,
    socket_manager: SocketConnectionManager,
) -> None:
    @sio.on('pomodoro.state.get')
    async def pomodoro_state_get(sid: str, _data: dict | None = None):
        return await _handle_pomodoro_state_get(socket_manager, sid)

    @sio.on('pomodoro.settings.update')
    async def pomodoro_settings_update(sid: str, data: dict | None):
        return await _handle_pomodoro_settings_update(
            socket_manager,
            sid,
            data,
        )

    @sio.on('pomodoro.start')
    async def pomodoro_start(sid: str, _data: dict | None = None):
        return await _handle_pomodoro_start(socket_manager, sid)

    @sio.on('pomodoro.pause')
    async def pomodoro_pause(sid: str, _data: dict | None = None):
        return await _handle_pomodoro_pause(socket_manager, sid)

    @sio.on('pomodoro.reset')
    async def pomodoro_reset(sid: str, _data: dict | None = None):
        return await _handle_pomodoro_reset(socket_manager, sid)
