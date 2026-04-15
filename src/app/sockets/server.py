import socketio
from fastapi import FastAPI

from src.app.sockets.manager import SocketConnectionManager

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # TODO: restrict in production
)

socket_manager = SocketConnectionManager(sio=sio)


def create_socket_app(fastapi_app: FastAPI):
    return socketio.ASGIApp(
        socketio_server=sio, other_asgi_app=fastapi_app, socketio_path='socket.io'
    )
