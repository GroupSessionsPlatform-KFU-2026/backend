import socketio
from fastapi import FastAPI
from socketio.exceptions import ConnectionRefusedError as SocketConnectionRefusedError

from src.app.sockets.auth import authenticate_socket_connection
from src.app.sockets.events import register_chat_events
from src.app.sockets.manager import SocketConnectionManager

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # TODO: restrict in production
    logger=True,
    engineio_logger=True,
)

socket_manager = SocketConnectionManager(sio=sio)


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None):
    _ = environ
    await socket_manager.register_connection(sid)

    try:
        context = await authenticate_socket_connection(auth)

        await socket_manager.attach_identity(
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
    await socket_manager.disconnect(sid)


register_chat_events(sio=sio, socket_manager=socket_manager)


def create_socket_app(fastapi_app: FastAPI):
    return socketio.ASGIApp(
        socketio_server=sio,
        other_asgi_app=fastapi_app,
        socketio_path='socket.io',
    )
