from dataclasses import dataclass
from typing import Any
from uuid import UUID

import socketio


@dataclass(slots=True)
class ConnectedClient:
    sid: str
    user_id: UUID | None = None
    room_id: UUID | None = None
    role: str | None = None


class SocketConnectionManager:
    def __init__(self, sio: socketio.AsyncServer):
        self._sio = sio
        self._clients: dict[str, ConnectedClient] = {}

    @staticmethod
    def build_room_channel(room_id: UUID) -> str:
        return f'room:{room_id}'

    def get_client(self, sid: str) -> ConnectedClient | None:
        return self._clients.get(sid)

    def list_clients_in_room(self, room_id: UUID) -> list[ConnectedClient]:
        return [
            client
            for client in self._clients.values()
            if client.room_id == room_id and client.user_id is not None
        ]

    def list_unique_users_in_room(self, room_id: UUID) -> list[ConnectedClient]:
        seen_user_ids: set[UUID] = set()
        unique_clients: list[ConnectedClient] = []

        for client in self.list_clients_in_room(room_id):
            if client.user_id is None:
                continue
            if client.user_id in seen_user_ids:
                continue

            seen_user_ids.add(client.user_id)
            unique_clients.append(client)

        return unique_clients

    def count_user_connections_in_room(self, room_id: UUID, user_id: UUID) -> int:
        return sum(
            1
            for client in self._clients.values()
            if client.room_id == room_id and client.user_id == user_id
        )

    @staticmethod
    def serialize_client(client: ConnectedClient) -> dict[str, str]:
        return {
            'user_id': str(client.user_id) if client.user_id else '',
            'room_id': str(client.room_id) if client.room_id else '',
            'role': client.role or '',
        }

    def build_presence_snapshot(self, room_id: UUID) -> dict[str, Any]:
        users = self.list_unique_users_in_room(room_id)
        return {
            'room_id': str(room_id),
            'count': len(users),
            'participants': [self.serialize_client(client) for client in users],
        }

    async def register_connection(self, sid: str) -> ConnectedClient:
        client = ConnectedClient(sid=sid)
        self._clients[sid] = client
        return client

    async def attach_identity(
        self,
        sid: str,
        user_id: UUID,
        room_id: UUID,
        role: str,
    ) -> ConnectedClient:
        client = self._clients.get(sid) or ConnectedClient(sid=sid)
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

    async def disconnect(self, sid: str) -> ConnectedClient | None:
        client = self._clients.pop(sid, None)

        if client is not None and client.room_id is not None:
            await self.leave_room(sid=sid, room_id=client.room_id)

        return client
