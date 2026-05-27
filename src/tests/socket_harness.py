from typing import Any, override

import socketio


class RecordingSocketServer(socketio.AsyncServer):
    def __init__(self) -> None:
        super().__init__(async_mode='asgi')
        self.sessions: dict[str, dict[str, Any]] = {}
        self.emitted: list[dict[str, Any]] = []

    async def save_session(
        self,
        sid: str,
        session: dict[str, Any],
        namespace: str | None = None,
    ) -> None:
        _ = namespace
        self.sessions[sid] = session

    async def get_session(
        self,
        sid: str,
        namespace: str | None = None,
    ) -> dict[str, Any]:
        _ = namespace
        return self.sessions.get(sid, {})

    @override
    async def emit(
        self,
        event: str,
        data: Any = None,
        to: str | None = None,
        room: str | None = None,
        skip_sid: str | None = None,
        namespace: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.emitted.append(
            {
                'event': event,
                'data': data,
                'to': to,
                'room': room,
                'skip_sid': skip_sid,
                'namespace': namespace,
                'extra': kwargs,
            }
        )
