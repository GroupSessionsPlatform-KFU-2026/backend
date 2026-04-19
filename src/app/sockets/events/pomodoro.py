from typing import Any

import socketio

from src.app.models.pomodoro_session import PomodoroSessionUpdate
from src.app.sockets.events.common import (
    ensure_role,
    ensure_room_is_active,
    ok_response,
    register_event_handlers,
    require_identity,
    require_payload_dict,
    require_scope,
)
from src.app.sockets.events.contexts import socket_service_factory
from src.app.sockets.manager import SocketConnectionManager


class PomodoroSocketError(Exception):
    pass


def _require_positive_int(raw_value: Any, field_name: str) -> int:
    if not isinstance(raw_value, int):
        raise PomodoroSocketError(f'Field "{field_name}" must be an integer')

    if raw_value <= 0:
        raise PomodoroSocketError(f'Field "{field_name}" must be greater than 0')

    return raw_value


def _parse_settings_update(payload: dict[str, Any]) -> PomodoroSessionUpdate:
    return PomodoroSessionUpdate(
        work_duration=_require_positive_int(
            payload.get('work_duration'), 'work_duration'
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


async def _get_state_payload(room_id, pomodoro_service):
    pomodoro = await pomodoro_service.get_room_pomodoro(room_id)
    if pomodoro is None:
        raise PomodoroSocketError('Pomodoro session not found')
    return pomodoro.model_dump(mode='json')


async def _emit_state_update(socket_manager, room_id, payload):
    await socket_manager.emit_to_room(
        room_id=room_id,
        event='pomodoro.state.updated',
        data=payload,
    )


async def _handle_state_get(
    socket_manager: SocketConnectionManager,
    sid: str,
    _data: dict | None = None,
) -> dict[str, object]:
    identity = await require_identity(socket_manager, sid, PomodoroSocketError)
    require_scope(identity, 'pomodoro:read', PomodoroSocketError)

    async with socket_service_factory.pomodoro() as (room_repository, pomodoro_service):
        await ensure_room_is_active(
            room_repository, identity.room_id, PomodoroSocketError
        )
        state_payload = await _get_state_payload(identity.room_id, pomodoro_service)

    return ok_response(state=state_payload)


async def _handle_settings_update(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, object]:
    payload = require_payload_dict(data, PomodoroSocketError)
    identity = await require_identity(socket_manager, sid, PomodoroSocketError)
    require_scope(identity, 'pomodoro:write', PomodoroSocketError)
    ensure_role(
        identity,
        {'owner', 'moderator'},
        'Only owner or moderator can control pomodoro',
        PomodoroSocketError,
    )

    pomodoro_update = _parse_settings_update(payload)

    async with socket_service_factory.pomodoro() as (room_repository, pomodoro_service):
        await ensure_room_is_active(
            room_repository, identity.room_id, PomodoroSocketError
        )

        updated_pomodoro = await pomodoro_service.update_room_pomodoro(
            room_id=identity.room_id,
            pomodoro_update=pomodoro_update,
        )
        if updated_pomodoro is None:
            raise PomodoroSocketError('Pomodoro session not found')

    state_payload = updated_pomodoro.model_dump(mode='json')
    await _emit_state_update(socket_manager, identity.room_id, state_payload)

    return ok_response(state=state_payload)


async def _handle_start(
    socket_manager: SocketConnectionManager,
    sid: str,
    _data: dict | None = None,
) -> dict[str, object]:
    identity = await require_identity(socket_manager, sid, PomodoroSocketError)
    require_scope(identity, 'pomodoro:write', PomodoroSocketError)
    ensure_role(
        identity,
        {'owner', 'moderator'},
        'Only owner or moderator can control pomodoro',
        PomodoroSocketError,
    )

    async with socket_service_factory.pomodoro() as (room_repository, pomodoro_service):
        await ensure_room_is_active(
            room_repository, identity.room_id, PomodoroSocketError
        )

        started_pomodoro = await pomodoro_service.start_pomodoro(identity.room_id)
        if started_pomodoro is None:
            raise PomodoroSocketError('Pomodoro session not found')

    state_payload = started_pomodoro.model_dump(mode='json')
    await _emit_state_update(socket_manager, identity.room_id, state_payload)

    return ok_response(state=state_payload)


async def _handle_pause(
    socket_manager: SocketConnectionManager,
    sid: str,
    _data: dict | None = None,
) -> dict[str, object]:
    identity = await require_identity(socket_manager, sid, PomodoroSocketError)
    require_scope(identity, 'pomodoro:write', PomodoroSocketError)
    ensure_role(
        identity,
        {'owner', 'moderator'},
        'Only owner or moderator can control pomodoro',
        PomodoroSocketError,
    )

    async with socket_service_factory.pomodoro() as (room_repository, pomodoro_service):
        await ensure_room_is_active(
            room_repository, identity.room_id, PomodoroSocketError
        )

        paused_pomodoro = await pomodoro_service.pause_pomodoro(identity.room_id)
        if paused_pomodoro is None:
            raise PomodoroSocketError('Pomodoro session not found')

    state_payload = paused_pomodoro.model_dump(mode='json')
    await _emit_state_update(socket_manager, identity.room_id, state_payload)

    return ok_response(state=state_payload)


async def _handle_reset(
    socket_manager: SocketConnectionManager,
    sid: str,
    _data: dict | None = None,
) -> dict[str, object]:
    identity = await require_identity(socket_manager, sid, PomodoroSocketError)
    require_scope(identity, 'pomodoro:write', PomodoroSocketError)
    ensure_role(
        identity,
        {'owner', 'moderator'},
        'Only owner or moderator can control pomodoro',
        PomodoroSocketError,
    )

    async with socket_service_factory.pomodoro() as (room_repository, pomodoro_service):
        await ensure_room_is_active(
            room_repository, identity.room_id, PomodoroSocketError
        )

        reset_pomodoro = await pomodoro_service.reset_pomodoro(identity.room_id)
        if reset_pomodoro is None:
            raise PomodoroSocketError('Pomodoro session not found')

    state_payload = reset_pomodoro.model_dump(mode='json')
    await _emit_state_update(socket_manager, identity.room_id, state_payload)

    return ok_response(state=state_payload)


def register_pomodoro_events(
    sio: socketio.AsyncServer,
    socket_manager: SocketConnectionManager,
) -> None:
    register_event_handlers(
        sio=sio,
        socket_manager=socket_manager,
        handlers={
            'pomodoro.state.get': _handle_state_get,
            'pomodoro.settings.update': _handle_settings_update,
            'pomodoro.start': _handle_start,
            'pomodoro.pause': _handle_pause,
            'pomodoro.reset': _handle_reset,
        },
        error_cls=PomodoroSocketError,
    )
