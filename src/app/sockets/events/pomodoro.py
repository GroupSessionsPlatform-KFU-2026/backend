from typing import Any
from uuid import UUID

import socketio

from src.app.models.pomodoro_session import PomodoroSessionUpdate
from src.app.sockets.events.common import (
    ensure_role,
    ensure_room_is_active,
    error_response,
    ok_response,
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


class PomodoroSocketEventHandler:
    def __init__(self, socket_manager: SocketConnectionManager) -> None:
        self._socket_manager = socket_manager

    def register(self, sio: socketio.AsyncServer) -> None:
        self._register_state_get(sio)
        self._register_settings_update(sio)
        self._register_start(sio)
        self._register_pause(sio)
        self._register_reset(sio)

    def _register_state_get(self, sio: socketio.AsyncServer) -> None:
        @sio.on('pomodoro.state.get')
        async def pomodoro_state_get(sid: str, _data: dict | None = None):
            try:
                return await self._handle_state_get(sid)
            except PomodoroSocketError as error:
                return error_response(str(error))

    def _register_settings_update(self, sio: socketio.AsyncServer) -> None:
        @sio.on('pomodoro.settings.update')
        async def pomodoro_settings_update(sid: str, data: dict | None):
            try:
                return await self._handle_settings_update(sid, data)
            except PomodoroSocketError as error:
                return error_response(str(error))

    def _register_start(self, sio: socketio.AsyncServer) -> None:
        @sio.on('pomodoro.start')
        async def pomodoro_start(sid: str, _data: dict | None = None):
            try:
                return await self._handle_start(sid)
            except PomodoroSocketError as error:
                return error_response(str(error))

    def _register_pause(self, sio: socketio.AsyncServer) -> None:
        @sio.on('pomodoro.pause')
        async def pomodoro_pause(sid: str, _data: dict | None = None):
            try:
                return await self._handle_pause(sid)
            except PomodoroSocketError as error:
                return error_response(str(error))

    def _register_reset(self, sio: socketio.AsyncServer) -> None:
        @sio.on('pomodoro.reset')
        async def pomodoro_reset(sid: str, _data: dict | None = None):
            try:
                return await self._handle_reset(sid)
            except PomodoroSocketError as error:
                return error_response(str(error))

    async def _emit_state_update(
        self,
        room_id: UUID,
        payload: dict[str, object],
    ) -> None:
        await self._socket_manager.emit_to_room(
            room_id=room_id,
            event='pomodoro.state.updated',
            data=payload,
        )

    async def _handle_state_get(self, sid: str) -> dict[str, object]:
        identity = await require_identity(
            self._socket_manager,
            sid,
            PomodoroSocketError,
        )
        require_scope(identity, 'pomodoro:read', PomodoroSocketError)

        async with socket_service_factory.pomodoro() as (
            room_repository,
            pomodoro_service,
        ):
            await ensure_room_is_active(
                room_repository,
                identity.room_id,
                PomodoroSocketError,
            )
            pomodoro = await pomodoro_service.get_room_pomodoro(identity.room_id)
            if pomodoro is None:
                raise PomodoroSocketError('Pomodoro session not found')

        state_payload = pomodoro.model_dump(mode='json')
        return ok_response(state=state_payload)

    async def _handle_settings_update(
        self,
        sid: str,
        data: dict | None,
    ) -> dict[str, object]:
        payload = require_payload_dict(data, PomodoroSocketError)
        identity = await require_identity(
            self._socket_manager,
            sid,
            PomodoroSocketError,
        )
        require_scope(identity, 'pomodoro:write', PomodoroSocketError)
        ensure_role(
            identity,
            {'owner', 'moderator'},
            'Only owner or moderator can control pomodoro',
            PomodoroSocketError,
        )

        pomodoro_update = _parse_settings_update(payload)

        async with socket_service_factory.pomodoro() as (
            room_repository,
            pomodoro_service,
        ):
            await ensure_room_is_active(
                room_repository,
                identity.room_id,
                PomodoroSocketError,
            )
            updated_pomodoro = await pomodoro_service.update_room_pomodoro(
                room_id=identity.room_id,
                pomodoro_update=pomodoro_update,
            )
            if updated_pomodoro is None:
                raise PomodoroSocketError('Pomodoro session not found')

        state_payload = updated_pomodoro.model_dump(mode='json')
        await self._emit_state_update(identity.room_id, state_payload)
        return ok_response(state=state_payload)

    async def _handle_start(self, sid: str) -> dict[str, object]:
        identity = await require_identity(
            self._socket_manager,
            sid,
            PomodoroSocketError,
        )
        require_scope(identity, 'pomodoro:write', PomodoroSocketError)
        ensure_role(
            identity,
            {'owner', 'moderator'},
            'Only owner or moderator can control pomodoro',
            PomodoroSocketError,
        )

        async with socket_service_factory.pomodoro() as (
            room_repository,
            pomodoro_service,
        ):
            await ensure_room_is_active(
                room_repository,
                identity.room_id,
                PomodoroSocketError,
            )
            started_pomodoro = await pomodoro_service.start_pomodoro(
                identity.room_id,
            )
            if started_pomodoro is None:
                raise PomodoroSocketError('Pomodoro session not found')

        state_payload = started_pomodoro.model_dump(mode='json')
        await self._emit_state_update(identity.room_id, state_payload)
        return ok_response(state=state_payload)

    async def _handle_pause(self, sid: str) -> dict[str, object]:
        identity = await require_identity(
            self._socket_manager,
            sid,
            PomodoroSocketError,
        )
        require_scope(identity, 'pomodoro:write', PomodoroSocketError)
        ensure_role(
            identity,
            {'owner', 'moderator'},
            'Only owner or moderator can control pomodoro',
            PomodoroSocketError,
        )

        async with socket_service_factory.pomodoro() as (
            room_repository,
            pomodoro_service,
        ):
            await ensure_room_is_active(
                room_repository,
                identity.room_id,
                PomodoroSocketError,
            )
            paused_pomodoro = await pomodoro_service.pause_pomodoro(
                identity.room_id,
            )
            if paused_pomodoro is None:
                raise PomodoroSocketError('Pomodoro session not found')

        state_payload = paused_pomodoro.model_dump(mode='json')
        await self._emit_state_update(identity.room_id, state_payload)
        return ok_response(state=state_payload)

    async def _handle_reset(self, sid: str) -> dict[str, object]:
        identity = await require_identity(
            self._socket_manager,
            sid,
            PomodoroSocketError,
        )
        require_scope(identity, 'pomodoro:write', PomodoroSocketError)
        ensure_role(
            identity,
            {'owner', 'moderator'},
            'Only owner or moderator can control pomodoro',
            PomodoroSocketError,
        )

        async with socket_service_factory.pomodoro() as (
            room_repository,
            pomodoro_service,
        ):
            await ensure_room_is_active(
                room_repository,
                identity.room_id,
                PomodoroSocketError,
            )
            reset_pomodoro = await pomodoro_service.reset_pomodoro(
                identity.room_id,
            )
            if reset_pomodoro is None:
                raise PomodoroSocketError('Pomodoro session not found')

        state_payload = reset_pomodoro.model_dump(mode='json')
        await self._emit_state_update(identity.room_id, state_payload)
        return ok_response(state=state_payload)
