from uuid import UUID

import socketio

from src.app.models.board_element_comment import (
    BoardElementCommentCreate,
    BoardElementCommentUpdate,
)
from src.app.sockets.events.common import (
    ensure_can_manage_resource,
    ensure_room_is_active,
    ok_response,
    parse_uuid,
    register_event_handlers,
    require_identity,
    require_non_empty_string,
    require_payload_dict,
    require_scope,
)
from src.app.sockets.events.contexts import board_comment_context
from src.app.sockets.manager import SocketConnectionManager


class BoardCommentSocketError(Exception):
    pass


def _parse_create_payload(payload: dict) -> tuple[UUID, str]:
    element_id = parse_uuid(
        payload.get('element_id'), 'element id', BoardCommentSocketError
    )
    content = require_non_empty_string(
        payload.get('content'),
        'content',
        BoardCommentSocketError,
    )
    return element_id, content


def _parse_update_payload(payload: dict) -> tuple[UUID, UUID, str]:
    element_id = parse_uuid(
        payload.get('element_id'), 'element id', BoardCommentSocketError
    )
    comment_id = parse_uuid(
        payload.get('comment_id'), 'comment id', BoardCommentSocketError
    )
    content = require_non_empty_string(
        payload.get('content'),
        'content',
        BoardCommentSocketError,
    )
    return element_id, comment_id, content


def _parse_delete_payload(payload: dict) -> tuple[UUID, UUID]:
    element_id = parse_uuid(
        payload.get('element_id'), 'element id', BoardCommentSocketError
    )
    comment_id = parse_uuid(
        payload.get('comment_id'), 'comment id', BoardCommentSocketError
    )
    return element_id, comment_id


async def _handle_comment_create(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, object]:
    payload = require_payload_dict(data, BoardCommentSocketError)
    identity = await require_identity(socket_manager, sid, BoardCommentSocketError)
    require_scope(identity, 'board:write', BoardCommentSocketError)

    element_id, content = _parse_create_payload(payload)

    async with board_comment_context() as (room_repository, comment_service):
        await ensure_room_is_active(
            room_repository, identity.room_id, BoardCommentSocketError
        )

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

    return ok_response(comment=comment_payload)


async def _handle_comment_update(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, object]:
    payload = require_payload_dict(data, BoardCommentSocketError)
    identity = await require_identity(socket_manager, sid, BoardCommentSocketError)
    require_scope(identity, 'board:write', BoardCommentSocketError)

    element_id, comment_id, content = _parse_update_payload(payload)

    async with board_comment_context() as (room_repository, comment_service):
        await ensure_room_is_active(
            room_repository, identity.room_id, BoardCommentSocketError
        )

        existing_comment = await comment_service.get_comment_in_element(
            room_id=identity.room_id,
            element_id=element_id,
            comment_id=comment_id,
        )
        if existing_comment is None:
            raise BoardCommentSocketError('Comment not found')

        ensure_can_manage_resource(
            author_id=existing_comment.author_id,
            identity=identity,
            message='You cannot edit this comment',
            error_cls=BoardCommentSocketError,
        )

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

    return ok_response(comment=comment_payload)


async def _handle_comment_delete(
    socket_manager: SocketConnectionManager,
    sid: str,
    data: dict | None,
) -> dict[str, object]:
    payload = require_payload_dict(data, BoardCommentSocketError)
    identity = await require_identity(socket_manager, sid, BoardCommentSocketError)
    require_scope(identity, 'board:delete', BoardCommentSocketError)

    element_id, comment_id = _parse_delete_payload(payload)

    async with board_comment_context() as (room_repository, comment_service):
        await ensure_room_is_active(
            room_repository, identity.room_id, BoardCommentSocketError
        )

        existing_comment = await comment_service.get_comment_in_element(
            room_id=identity.room_id,
            element_id=element_id,
            comment_id=comment_id,
        )
        if existing_comment is None:
            raise BoardCommentSocketError('Comment not found')

        ensure_can_manage_resource(
            author_id=existing_comment.author_id,
            identity=identity,
            message='You cannot delete this comment',
            error_cls=BoardCommentSocketError,
        )

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
    }

    await socket_manager.emit_to_room(
        room_id=identity.room_id,
        event='board.comment.deleted',
        data=deleted_payload,
    )

    return ok_response(deleted_comment_id=str(comment_id))


def register_board_comment_events(
    sio: socketio.AsyncServer,
    socket_manager: SocketConnectionManager,
) -> None:
    register_event_handlers(
        sio=sio,
        socket_manager=socket_manager,
        handlers={
            'board.comment.create': _handle_comment_create,
            'board.comment.update': _handle_comment_update,
            'board.comment.delete': _handle_comment_delete,
        },
        error_cls=BoardCommentSocketError,
    )
