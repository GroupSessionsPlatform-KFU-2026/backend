from uuid import UUID

from src.app.sockets.manager import ConnectedClient, SocketConnectionManager


async def emit_presence_snapshot_to_room(
    socket_manager: SocketConnectionManager,
    room_id: UUID,
) -> None:
    snapshot = socket_manager.build_presence_snapshot(room_id)
    await socket_manager.emit_to_room(
        room_id=room_id,
        event='room.presence.snapshot',
        data=snapshot,
    )


async def emit_participant_joined(
    socket_manager: SocketConnectionManager,
    client: ConnectedClient,
    skip_sid: str | None = None,
) -> None:
    if client.room_id is None or client.user_id is None:
        return

    payload = socket_manager.serialize_client(client)
    await socket_manager.emit_to_room(
        room_id=client.room_id,
        event='participant.joined',
        data=payload,
        skip_sid=skip_sid,
    )


async def emit_participant_left(
    socket_manager: SocketConnectionManager,
    client: ConnectedClient,
) -> None:
    if client.room_id is None or client.user_id is None:
        return

    payload = socket_manager.serialize_client(client)
    await socket_manager.emit_to_room(
        room_id=client.room_id,
        event='participant.left',
        data=payload,
    )


async def emit_room_ended_and_disconnect(
    socket_manager: SocketConnectionManager,
    room_id: UUID,
) -> None:
    payload = {'room_id': str(room_id)}
    clients = list(socket_manager.list_clients_in_room(room_id))

    await socket_manager.emit_to_room(
        room_id=room_id,
        event='room.ended',
        data=payload,
    )

    for client in clients:
        await socket_manager.force_disconnect(client.sid)
