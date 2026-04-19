import socketio
from fastapi import FastAPI
from socketio.exceptions import ConnectionRefusedError as SocketConnectionRefusedError

from src.app.core.settings import settings
from src.app.sockets.auth import authenticate_socket_connection
from src.app.sockets.events import (
    BoardCommentSocketEventHandler,
    BoardSocketEventHandler,
    ChatSocketEventHandler,
    PomodoroSocketEventHandler,
    emit_participant_joined,
    emit_participant_left,
    emit_presence_snapshot_to_room,
)
from src.app.sockets.manager import SocketConnectionManager

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.socket.cors_allowed_origins,
)

socket_manager = SocketConnectionManager(sio=sio)


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None):
    _ = environ

    await socket_manager.register_connection(sid)

    try:
        context = await authenticate_socket_connection(auth)

        client = await socket_manager.attach_identity(
            sid=sid,
            user_id=context.user_id,
            room_id=context.room_id,
            role=context.role,
        )

        await socket_manager.save_socket_session(
            sid=sid,
            data={
                'user_id': str(context.user_id),
                'room_id': str(context.room_id),
                'role': context.role,
                'scopes': context.scopes,
            },
        )

        await socket_manager.join_room(
            sid=sid,
            room_id=context.room_id,
        )

        user_connections = socket_manager.count_user_connections_in_room(
            room_id=context.room_id,
            user_id=context.user_id,
        )
        is_first_connection_for_user = user_connections == 1

        if is_first_connection_for_user:
            await emit_participant_joined(
                socket_manager=socket_manager,
                client=client,
                skip_sid=sid,
            )

        await emit_presence_snapshot_to_room(
            socket_manager=socket_manager,
            room_id=context.room_id,
        )

        return True

    except SocketConnectionRefusedError:
        await socket_manager.disconnect(sid)
        raise

    except Exception as error:
        await socket_manager.disconnect(sid)
        raise SocketConnectionRefusedError('Socket authentication failed') from error


@sio.event
async def disconnect(sid: str, reason: str):
    _ = reason

    client = socket_manager.get_client(sid)
    if client is None:
        await socket_manager.disconnect(sid)
        return

    room_id = client.room_id
    user_id = client.user_id

    await socket_manager.disconnect(sid)

    if room_id is None or user_id is None:
        return

    remaining_connections = socket_manager.count_user_connections_in_room(
        room_id=room_id,
        user_id=user_id,
    )
    is_last_connection_for_user = remaining_connections == 0

    if is_last_connection_for_user:
        await emit_participant_left(
            socket_manager=socket_manager,
            client=client,
        )

    await emit_presence_snapshot_to_room(
        socket_manager=socket_manager,
        room_id=room_id,
    )


BoardSocketEventHandler(socket_manager).register(sio)
BoardCommentSocketEventHandler(socket_manager).register(sio)
ChatSocketEventHandler(socket_manager).register(sio)
PomodoroSocketEventHandler(socket_manager).register(sio)


def create_socket_app(fastapi_app: FastAPI):
    return socketio.ASGIApp(
        socketio_server=sio,
        other_asgi_app=fastapi_app,
        socketio_path=settings.socket.path,
    )
