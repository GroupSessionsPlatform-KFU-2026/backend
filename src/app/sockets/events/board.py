from typing import Any
from uuid import UUID

import socketio
from pydantic import ValidationError

from src.app.models.board_element import BoardElementCreate, BoardElementUpdate
from src.app.schemas.board_elements_filters import BoardElementType
from src.app.services.board_elements import BoardElementService
from src.app.sockets.events.base_room_crud import BaseRoomCrudSocketHandler
from src.app.sockets.events.common import (
    SocketIdentity,
    parse_uuid,
    register_event_handlers,
)
from src.app.sockets.events.contexts import socket_service_factory
from src.app.sockets.manager import SocketConnectionManager


class BoardSocketError(Exception):
    pass


def _require_data_object(raw_data: Any) -> dict[str, Any]:
    if not isinstance(raw_data, dict):
        raise BoardSocketError('Field "data" must be an object')
    return raw_data


class BoardSocketHandler(
    BaseRoomCrudSocketHandler[
        BoardElementService, BoardElementCreate, BoardElementUpdate
    ]
):
    write_scope = 'board:write'
    delete_scope = 'board:delete'

    created_event = 'board.element.created'
    updated_event = 'board.element.updated'
    deleted_event = 'board.element.deleted'

    resource_response_key = 'element'
    deleted_response_key = 'deleted_element_id'

    create_target_not_found_message = 'Element not found'
    resource_not_found_message = 'Element not found'
    update_forbidden_message = 'You cannot edit this element'
    delete_forbidden_message = 'You cannot delete this element'

    def parse_create_payload(
        self,
        payload: dict[str, Any],
        identity: SocketIdentity,
    ) -> BoardElementCreate:
        try:
            return BoardElementCreate(
                room_id=identity.room_id,
                author_id=identity.user_id,
                element_type=BoardElementType(payload.get('element_type')),
                data=_require_data_object(payload.get('data')),
            )
        except (ValidationError, ValueError, TypeError) as error:
            raise BoardSocketError(f'Invalid board payload: {error}') from error

    def parse_update_payload(
        self,
        payload: dict[str, Any],
    ) -> tuple[dict[str, UUID], BoardElementUpdate]:
        element_id = parse_uuid(
            payload.get('element_id'),
            'element id',
            BoardSocketError,
        )

        try:
            element_update = BoardElementUpdate(
                element_type=BoardElementType(payload.get('element_type')),
                data=_require_data_object(payload.get('data')),
            )
        except (ValidationError, ValueError, TypeError) as error:
            raise BoardSocketError(f'Invalid board payload: {error}') from error

        return {'element_id': element_id}, element_update

    def parse_delete_payload(
        self,
        payload: dict[str, Any],
    ) -> dict[str, UUID]:
        element_id = parse_uuid(
            payload.get('element_id'),
            'element id',
            BoardSocketError,
        )
        return {'element_id': element_id}

    async def create_resource(
        self,
        service: BoardElementService,
        identity: SocketIdentity,
        payload: BoardElementCreate,
    ):
        return await service.create_element(
            room_id=identity.room_id,
            element_create=payload,
        )

    async def get_existing_resource(
        self,
        service: BoardElementService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ):
        return await service.get_element_in_room(
            room_id=identity.room_id,
            element_id=resource_ids['element_id'],
        )

    async def update_resource(
        self,
        service: BoardElementService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
        payload: BoardElementUpdate,
    ):
        return await service.update_element(
            room_id=identity.room_id,
            element_id=resource_ids['element_id'],
            element_update=payload,
        )

    async def delete_resource(
        self,
        service: BoardElementService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ):
        return await service.delete_element(
            room_id=identity.room_id,
            element_id=resource_ids['element_id'],
        )

    def get_author_id(self, resource) -> UUID:
        return resource.author_id

    def build_deleted_event_payload(
        self,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> dict[str, Any]:
        return {
            'id': str(resource_ids['element_id']),
            'room_id': str(identity.room_id),
            'is_deleted': True,
        }

    def get_deleted_id(self, resource_ids: dict[str, UUID]) -> UUID:
        return resource_ids['element_id']


def register_board_events(
    sio: socketio.AsyncServer,
    socket_manager: SocketConnectionManager,
) -> None:
    handler = BoardSocketHandler(
        socket_manager=socket_manager,
        context_factory=socket_service_factory.board,
        error_cls=BoardSocketError,
    )

    register_event_handlers(
        sio=sio,
        socket_manager=socket_manager,
        handlers={
            'board.element.create': handler.handle_create,
            'board.element.update': handler.handle_update,
            'board.element.delete': handler.handle_delete,
        },
        error_cls=BoardSocketError,
    )
