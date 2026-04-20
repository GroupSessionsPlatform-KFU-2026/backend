from typing import Any
from uuid import UUID

from src.app.models.board_element_comment import (
    BoardElementComment,
    BoardElementCommentCreate,
    BoardElementCommentUpdate,
)
from src.app.services.board_elements_comments import BoardElementCommentService
from src.app.sockets.events.base_room_crud import BaseRoomCrudSocketHandler
from src.app.sockets.events.common import (
    SocketIdentity,
    parse_uuid,
    require_non_empty_string,
)
from src.app.sockets.events.contexts import socket_service_factory
from src.app.sockets.manager import SocketConnectionManager


class BoardCommentSocketError(Exception):
    pass


class BoardCommentSocketEventHandler(
    BaseRoomCrudSocketHandler[
        BoardElementCommentService,
        BoardElementCommentCreate,
        BoardElementCommentUpdate,
    ]
):
    _create_command = 'board.comment.create'
    _update_command = 'board.comment.update'
    _delete_command = 'board.comment.delete'

    _write_scope = 'board:write'
    _delete_scope = 'board:delete'

    _created_event = 'board.comment.created'
    _updated_event = 'board.comment.updated'
    _deleted_event = 'board.comment.deleted'

    _resource_response_key = 'comment'
    _deleted_response_key = 'deleted_comment_id'

    _create_target_not_found_message = 'Board element not found'
    _resource_not_found_message = 'Comment not found'
    _update_forbidden_message = 'You cannot edit this comment'
    _delete_forbidden_message = 'You cannot delete this comment'

    def __init__(self, socket_manager: SocketConnectionManager) -> None:
        super().__init__(
            socket_manager=socket_manager,
            context_factory=socket_service_factory.board_comments,
            error_cls=BoardCommentSocketError,
        )

    def _parse_create_payload(
        self,
        payload: dict[str, Any],
        identity: SocketIdentity,
    ) -> BoardElementCommentCreate:
        element_id = parse_uuid(
            payload.get('element_id'),
            'element id',
            BoardCommentSocketError,
        )
        content = require_non_empty_string(
            payload.get('content'),
            'content',
            BoardCommentSocketError,
        )
        return BoardElementCommentCreate(
            board_element_id=element_id,
            author_id=identity.user_id,
            content=content,
        )

    def _parse_update_payload(
        self,
        payload: dict[str, Any],
    ) -> tuple[dict[str, UUID], BoardElementCommentUpdate]:
        element_id = parse_uuid(
            payload.get('element_id'),
            'element id',
            BoardCommentSocketError,
        )
        comment_id = parse_uuid(
            payload.get('comment_id'),
            'comment id',
            BoardCommentSocketError,
        )
        content = require_non_empty_string(
            payload.get('content'),
            'content',
            BoardCommentSocketError,
        )
        return (
            {
                'element_id': element_id,
                'comment_id': comment_id,
            },
            BoardElementCommentUpdate(content=content),
        )

    def _parse_delete_payload(
        self,
        payload: dict[str, Any],
    ) -> dict[str, UUID]:
        element_id = parse_uuid(
            payload.get('element_id'),
            'element id',
            BoardCommentSocketError,
        )
        comment_id = parse_uuid(
            payload.get('comment_id'),
            'comment id',
            BoardCommentSocketError,
        )
        return {
            'element_id': element_id,
            'comment_id': comment_id,
        }

    async def _create_resource(
        self,
        service: BoardElementCommentService,
        identity: SocketIdentity,
        payload: BoardElementCommentCreate,
    ) -> BoardElementComment | None:
        return await service.create_comment(
            room_id=identity.room_id,
            element_id=payload.board_element_id,
            comment_create=payload,
        )

    async def _get_existing_resource(
        self,
        service: BoardElementCommentService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> BoardElementComment | None:
        return await service.get_comment_in_element(
            room_id=identity.room_id,
            element_id=resource_ids['element_id'],
            comment_id=resource_ids['comment_id'],
        )

    async def _update_resource(
        self,
        service: BoardElementCommentService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
        payload: BoardElementCommentUpdate,
    ) -> BoardElementComment | None:
        return await service.update_comment(
            room_id=identity.room_id,
            element_id=resource_ids['element_id'],
            comment_id=resource_ids['comment_id'],
            comment_update=payload,
        )

    async def _delete_resource(
        self,
        service: BoardElementCommentService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> BoardElementComment | None:
        return await service.delete_comment(
            room_id=identity.room_id,
            element_id=resource_ids['element_id'],
            comment_id=resource_ids['comment_id'],
        )

    def _get_author_id(self, resource: BoardElementComment) -> UUID:
        return resource.author_id

    def _build_deleted_event_payload(
        self,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> dict[str, Any]:
        return {
            'id': str(resource_ids['comment_id']),
            'board_element_id': str(resource_ids['element_id']),
            'room_id': str(identity.room_id),
            'is_deleted': True,
        }

    def _get_deleted_id(self, resource_ids: dict[str, UUID]) -> UUID:
        return resource_ids['comment_id']
