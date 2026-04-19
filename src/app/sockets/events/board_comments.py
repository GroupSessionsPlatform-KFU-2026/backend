from typing import Any
from uuid import UUID

import socketio

from src.app.models.board_element_comment import (
    BoardElementCommentCreate,
    BoardElementCommentUpdate,
)
from src.app.services.board_elements_comments import BoardElementCommentService
from src.app.sockets.events.base_room_crud import BaseRoomCrudSocketHandler
from src.app.sockets.events.common import (
    SocketIdentity,
    parse_uuid,
    register_event_handlers,
    require_non_empty_string,
)
from src.app.sockets.events.contexts import socket_service_factory
from src.app.sockets.manager import SocketConnectionManager


class BoardCommentSocketError(Exception):
    pass


class BoardCommentSocketHandler(
    BaseRoomCrudSocketHandler[
        BoardElementCommentService,
        BoardElementCommentCreate,
        BoardElementCommentUpdate,
    ]
):
    write_scope = 'board:write'
    delete_scope = 'board:delete'

    created_event = 'board.comment.created'
    updated_event = 'board.comment.updated'
    deleted_event = 'board.comment.deleted'

    resource_response_key = 'comment'
    deleted_response_key = 'deleted_comment_id'

    create_target_not_found_message = 'Board element not found'
    resource_not_found_message = 'Comment not found'
    update_forbidden_message = 'You cannot edit this comment'
    delete_forbidden_message = 'You cannot delete this comment'

    def parse_create_payload(
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

    def parse_update_payload(
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

    def parse_delete_payload(
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

    async def create_resource(
        self,
        service: BoardElementCommentService,
        identity: SocketIdentity,
        payload: BoardElementCommentCreate,
    ):
        return await service.create_comment(
            room_id=identity.room_id,
            element_id=payload.board_element_id,
            comment_create=payload,
        )

    async def get_existing_resource(
        self,
        service: BoardElementCommentService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ):
        return await service.get_comment_in_element(
            room_id=identity.room_id,
            element_id=resource_ids['element_id'],
            comment_id=resource_ids['comment_id'],
        )

    async def update_resource(
        self,
        service: BoardElementCommentService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
        payload: BoardElementCommentUpdate,
    ):
        return await service.update_comment(
            room_id=identity.room_id,
            element_id=resource_ids['element_id'],
            comment_id=resource_ids['comment_id'],
            comment_update=payload,
        )

    async def delete_resource(
        self,
        service: BoardElementCommentService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ):
        return await service.delete_comment(
            room_id=identity.room_id,
            element_id=resource_ids['element_id'],
            comment_id=resource_ids['comment_id'],
        )

    def get_author_id(self, resource) -> UUID:
        return resource.author_id

    def build_deleted_event_payload(
        self,
        _identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> dict[str, Any]:
        return {
            'id': str(resource_ids['comment_id']),
            'board_element_id': str(resource_ids['element_id']),
        }

    def get_deleted_id(self, resource_ids: dict[str, UUID]) -> UUID:
        return resource_ids['comment_id']


def register_board_comment_events(
    sio: socketio.AsyncServer,
    socket_manager: SocketConnectionManager,
) -> None:
    handler = BoardCommentSocketHandler(
        socket_manager=socket_manager,
        context_factory=socket_service_factory.board_comments,
        error_cls=BoardCommentSocketError,
    )

    register_event_handlers(
        sio=sio,
        socket_manager=socket_manager,
        handlers={
            'board.comment.create': handler.handle_create,
            'board.comment.update': handler.handle_update,
            'board.comment.delete': handler.handle_delete,
        },
        error_cls=BoardCommentSocketError,
    )
