from dataclasses import dataclass
from typing import Any
from uuid import UUID

import socketio

from src.app.dependencies.session import async_session_maker
from src.app.models.board_element import BoardElement
from src.app.models.board_element_comment import (
    BoardElementComment,
    BoardElementCommentCreate,
    BoardElementCommentUpdate,
)
from src.app.models.room import Room, RoomStatus
from src.app.services.board_elements_comments import BoardElementCommentService
from src.app.sockets.manager import SocketConnectionManager
from src.app.utils.repository import Repository


class BoardCommentSocketError(Exception):
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


def _has_scope(scopes: list[str], required_scope: str) -> bool:
    return required_scope in scopes


def _error_response(message: str) -> dict[str, Any]:
    return {'ok': False, 'error': message}


def _ok_response(**extra: Any) -> dict[str, Any]:
    return {'ok': True, **extra}


def _require_payload_dict(data: dict | None) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise BoardCommentSocketError('Invalid payload')
    return data


async def _require_identity(
    socket_manager: SocketConnectionManager,
    sid: str,
) -> SocketIdentity:
    identity = await _get_socket_identity(socket_manager, sid)
    if identity is None:
        raise BoardCommentSocketError('Socket session is not authenticated')
    return identity


def _require_scope(identity: SocketIdentity, required_scope: str) -> None:
    if not _has_scope(identity.scopes, required_scope):
        raise BoardCommentSocketError('Not enough permissions')


def _require_uuid(raw_value: Any, field_name: str) -> UUID:
    try:
        return UUID(str(raw_value))
    except ValueError as error:
        raise BoardCommentSocketError(f'Invalid {field_name}') from error


def _require_content(raw_content: Any) -> str:
    if not isinstance(raw_content, str):
        raise BoardCommentSocketError('Content must be a string')

    content = raw_content.strip()
    if not content:
        raise BoardCommentSocketError('Content cannot be empty')

    return content


def _build_services(
    db_session: Any,
) -> tuple[Repository[Room], BoardElementCommentService]:
    room_repository = Repository[Room](db_session)
    comment_repository = Repository[BoardElementComment](db_session)
    element_repository = Repository[BoardElement](db_session)

    comment_service = BoardElementCommentService(
        repository=comment_repository,
        board_element_repository=element_repository,
    )
    return room_repository, comment_service


async def _ensure_room_is_active(
    room_repository: Repository[Room],
    room_id: UUID,
) -> None:
    room = await room_repository.get(room_id)

    if room is None:
        raise BoardCommentSocketError('Room not found')

    if room.status == RoomStatus.ENDED:
        raise BoardCommentSocketError('Room already ended')


async def _require_existing_comment(
    comment_service: BoardElementCommentService,
    room_id: UUID,
    element_id: UUID,
    comment_id: UUID,
) -> BoardElementComment:
    existing_comment = await comment_service.get_comment_in_element(
        room_id=room_id,
        element_id=element_id,
        comment_id=comment_id,
    )

    if existing_comment is None:
        raise BoardCommentSocketError('Comment not found')

    return existing_comment


def _ensure_can_edit(
    existing_comment: BoardElementComment,
    identity: SocketIdentity,
) -> None:
    can_edit = existing_comment.author_id == identity.user_id or identity.role in {
        'owner',
        'moderator',
    }
    if not can_edit:
        raise BoardCommentSocketError('You cannot edit this comment')


def _ensure_can_delete(
    existing_comment: BoardElementComment,
    identity: SocketIdentity,
) -> None:
    can_delete = existing_comment.author_id == identity.user_id or identity.role in {
        'owner',
        'moderator',
    }

    if not can_delete:
        raise BoardCommentSocketError('You cannot delete this comment')


def _parse_create_payload(payload: dict[str, Any]) -> tuple[UUID, str]:
    element_id = _require_uuid(payload.get('element_id'), 'element id')
    content = _require_content(payload.get('content'))
    return element_id, content


def _parse_update_payload(
    payload: dict[str, Any],
) -> tuple[UUID, UUID, str]:
    element_id = _require_uuid(payload.get('element_id'), 'element id')
    comment_id = _require_uuid(payload.get('comment_id'), 'comment id')
    content = _require_content(payload.get('content'))
    return element_id, comment_id, content


def _parse_delete_payload(payload: dict[str, Any]) -> tuple[UUID, UUID]:
    element_id = _require_uuid(payload.get('element_id'), 'element id')
    comment_id = _require_uuid(payload.get('comment_id'), 'comment id')
    return element_id, comment_id


async def _handle_board_comment_create(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, Any]:
    try:
        payload = _require_payload_dict(data)
        identity = await _require_identity(socket_manager, sid)
        _require_scope(identity, 'board:write')

        element_id, content = _parse_create_payload(payload)

        async with async_session_maker() as db_session:
            room_repository, comment_service = _build_services(db_session)
            await _ensure_room_is_active(room_repository, identity.room_id)

            created_comment = await comment_service.create_comment(
                room_id=identity.room_id,
                element_id=element_id,
                comment_create=BoardElementCommentCreate(
                    board_element_id=element_id,
                    author_id=identity.user_id,
                    content=content,
                ),
            )

            if created_comment is None:
                raise BoardCommentSocketError('Board element not found')

        comment_payload = created_comment.model_dump(mode='json')

        await socket_manager.emit_to_room(
            room_id=identity.room_id,
            event='board.comment.created',
            data=comment_payload,
        )
    except BoardCommentSocketError as error:
        return _error_response(str(error))

    return _ok_response(comment=comment_payload)


async def _handle_board_comment_update(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, Any]:
    try:
        payload = _require_payload_dict(data)
        identity = await _require_identity(socket_manager, sid)
        _require_scope(identity, 'board:write')

        element_id, comment_id, content = _parse_update_payload(payload)

        async with async_session_maker() as db_session:
            room_repository, comment_service = _build_services(db_session)
            await _ensure_room_is_active(room_repository, identity.room_id)

            existing_comment = await _require_existing_comment(
                comment_service=comment_service,
                room_id=identity.room_id,
                element_id=element_id,
                comment_id=comment_id,
            )
            _ensure_can_edit(existing_comment, identity)

            updated_comment = await comment_service.update_comment(
                room_id=identity.room_id,
                element_id=element_id,
                comment_id=comment_id,
                comment_update=BoardElementCommentUpdate(content=content),
            )

            if updated_comment is None:
                raise BoardCommentSocketError('Comment not found')

        comment_payload = updated_comment.model_dump(mode='json')

        await socket_manager.emit_to_room(
            room_id=identity.room_id,
            event='board.comment.updated',
            data=comment_payload,
        )
    except BoardCommentSocketError as error:
        return _error_response(str(error))

    return _ok_response(comment=comment_payload)


async def _handle_board_comment_delete(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, Any]:
    try:
        payload = _require_payload_dict(data)
        identity = await _require_identity(socket_manager, sid)
        _require_scope(identity, 'board:delete')

        element_id, comment_id = _parse_delete_payload(payload)

        async with async_session_maker() as db_session:
            room_repository, comment_service = _build_services(db_session)
            await _ensure_room_is_active(room_repository, identity.room_id)

            existing_comment = await _require_existing_comment(
                comment_service=comment_service,
                room_id=identity.room_id,
                element_id=element_id,
                comment_id=comment_id,
            )
            _ensure_can_delete(existing_comment, identity)

            deleted_comment = await comment_service.delete_comment(
                room_id=identity.room_id,
                element_id=element_id,
                comment_id=comment_id,
            )

            if deleted_comment is None:
                raise BoardCommentSocketError('Comment not found')

        deleted_payload = {
            'id': str(comment_id),
            'board_element_id': str(element_id),
            'room_id': str(identity.room_id),
            'is_deleted': True,
        }

        await socket_manager.emit_to_room(
            room_id=identity.room_id,
            event='board.comment.deleted',
            data=deleted_payload,
        )
    except BoardCommentSocketError as error:
        return _error_response(str(error))

    return _ok_response(deleted_comment_id=str(comment_id))


def register_board_comment_events(
    sio: socketio.AsyncServer,
    socket_manager: SocketConnectionManager,
) -> None:
    @sio.on('board.comment.create')
    async def board_comment_create(sid: str, data: dict | None):
        return await _handle_board_comment_create(socket_manager, sid, data)

    @sio.on('board.comment.update')
    async def board_comment_update(sid: str, data: dict | None):
        return await _handle_board_comment_update(socket_manager, sid, data)

    @sio.on('board.comment.delete')
    async def board_comment_delete(sid: str, data: dict | None):
        return await _handle_board_comment_delete(socket_manager, sid, data)
