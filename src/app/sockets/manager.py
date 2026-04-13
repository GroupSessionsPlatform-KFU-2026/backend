from dataclasses import dataclass
from typing import Any
from uuid import UUID

import socketio


@dataclass(slots=True)
class ConnectionClient:
    sid: str
    user_id: UUID | None = None
    room_id: UUID | None = None
    role: str | None = None


class SocketConnectionManager:
    def __init__(self, sio: socketio.AsyncServer):
        self._sio = sio
        self._clients: dict[str, ConnectionClient] = {}

    @staticmethod
    def build_room_channel(room_id: UUID) -> str:
        return f'room:{room_id}'

    def get_client(self, sid: str) -> ConnectionClient | None:
        return self._clients.get(sid)

    async def register_connection(self, sid: str) -> ConnectionClient:
        client = ConnectionClient(sid=sid)
        self._clients[sid] = client
        return client

    # After auth
    async def attach_identity(
        self,
        sid: str,
        user_id: UUID,
        room_id: UUID,
        role: str,
    ) -> ConnectionClient:
        client = self._clients.get(sid) or ConnectionClient(sid=sid)
        client.user_id = user_id
        client.room_id = room_id
        client.role = role
        self._clients[sid] = client
        return client

    async def save_socket_session(self, sid: str, data: dict[str, Any]) -> None:
        await self._sio.save_session(sid, data)

    async def get_socket_session(self, sid: str) -> dict[str, Any]:
        session = await self._sio.get_session(sid)
        return dict(session) if session else {}

    async def join_room(self, sid: str, room_id: UUID) -> None:
        await self._sio.enter_room(
            sid=sid,
            room=self.build_room_channel(room_id),
        )

    async def leave_room(self, sid: str, room_id: UUID) -> None:
        await self._sio.leave_room(
            sid=sid,
            room=self.build_room_channel(room_id),
        )

    async def emit_to_room(
        self,
        room_id: UUID,
        event: str,
        data: dict[str, Any],
        skip_sid: str | None = None,
    ) -> None:
        await self._sio.emit(
            event=event,
            data=data,
            room=self.build_room_channel(room_id),
            skip_sid=skip_sid,
        )

    async def emit_to_client(
        self,
        sid: str,
        event: str,
        data: dict[str, Any],
    ) -> None:
        await self._sio.emit(
            event=event,
            data=data,
            to=sid,
        )

    async def disconnect(self, sid: str) -> ConnectionClient | None:
        client = self._clients.pop(sid, None)

        if client is not None and client.room_id is not None:
            await self.leave_room(sid=sid, room_id=client.room_id)

        return client
