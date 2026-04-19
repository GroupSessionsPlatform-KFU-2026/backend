from typing import Any
from uuid import UUID

from pydantic import ValidationError

from src.app.models.board_element import (
    BoardElement,
    BoardElementCreate,
    BoardElementUpdate,
)
from src.app.schemas.board_elements_filters import BoardElementType
from src.app.services.board_elements import BoardElementService
from src.app.sockets.events.base_room_crud import BaseRoomCrudSocketHandler
from src.app.sockets.events.common import SocketIdentity, parse_uuid
from src.app.sockets.events.contexts import socket_service_factory
from src.app.sockets.manager import SocketConnectionManager


class BoardSocketError(Exception):
    pass


def _require_data_object(raw_data: Any) -> dict[str, Any]:
    if not isinstance(raw_data, dict):
        raise BoardSocketError('Field "data" must be an object')
    return raw_data


class BoardSocketEventHandler(
    BaseRoomCrudSocketHandler[
        BoardElementService,
        BoardElementCreate,
        BoardElementUpdate,
    ]
):
    _create_command = 'board.element.create'
    _update_command = 'board.element.update'
    _delete_command = 'board.element.delete'

    _write_scope = 'board:write'
    _delete_scope = 'board:delete'

    _created_event = 'board.element.created'
    _updated_event = 'board.element.updated'
    _deleted_event = 'board.element.deleted'

    _resource_response_key = 'element'
    _deleted_response_key = 'deleted_element_id'

    _create_target_not_found_message = 'Room not found'
    _resource_not_found_message = 'Element not found'
    _update_forbidden_message = 'You cannot edit this element'
    _delete_forbidden_message = 'You cannot delete this element'

    def __init__(self, socket_manager: SocketConnectionManager) -> None:
        super().__init__(
            socket_manager=socket_manager,
            context_factory=socket_service_factory.board,
            error_cls=BoardSocketError,
        )

    def _parse_create_payload(
        self,
        payload: dict[str, Any],
        identity: SocketIdentity,
    ) -> BoardElementCreate:
        raw_element_type = payload.get('element_type')
        raw_element_data = _require_data_object(payload.get('data'))

        try:
            return BoardElementCreate(
                room_id=identity.room_id,
                author_id=identity.user_id,
                element_type=BoardElementType(raw_element_type),
                data=raw_element_data,
            )
        except (ValidationError, ValueError, TypeError) as error:
            raise BoardSocketError(f'Invalid board payload: {error}') from error

    def _parse_update_payload(
        self,
        payload: dict[str, Any],
    ) -> tuple[dict[str, UUID], BoardElementUpdate]:
        element_id = parse_uuid(
            payload.get('element_id'),
            'element id',
            BoardSocketError,
        )
        raw_element_type = payload.get('element_type')
        raw_element_data = _require_data_object(payload.get('data'))

        try:
            element_update = BoardElementUpdate(
                element_type=BoardElementType(raw_element_type),
                data=raw_element_data,
            )
        except (ValidationError, ValueError, TypeError) as error:
            raise BoardSocketError(f'Invalid board payload: {error}') from error

        return {'element_id': element_id}, element_update

    def _parse_delete_payload(
        self,
        payload: dict[str, Any],
    ) -> dict[str, UUID]:
        element_id = parse_uuid(
            payload.get('element_id'),
            'element id',
            BoardSocketError,
        )
        return {'element_id': element_id}

    async def _create_resource(
        self,
        service: BoardElementService,
        identity: SocketIdentity,
        payload: BoardElementCreate,
    ) -> BoardElement | None:
        return await service.create_element(
            room_id=identity.room_id,
            element_create=payload,
        )

    async def _get_existing_resource(
        self,
        service: BoardElementService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> BoardElement | None:
        return await service.get_element_in_room(
            room_id=identity.room_id,
            element_id=resource_ids['element_id'],
        )

    async def _update_resource(
        self,
        service: BoardElementService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
        payload: BoardElementUpdate,
    ) -> BoardElement | None:
        return await service.update_element(
            room_id=identity.room_id,
            element_id=resource_ids['element_id'],
            element_update=payload,
        )

    async def _delete_resource(
        self,
        service: BoardElementService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> BoardElement | None:
        return await service.delete_element(
            room_id=identity.room_id,
            element_id=resource_ids['element_id'],
        )

    def _get_author_id(self, resource: BoardElement) -> UUID:
        return resource.author_id

    def _build_deleted_event_payload(
        self,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> dict[str, Any]:
        return {
            'id': str(resource_ids['element_id']),
            'room_id': str(identity.room_id),
            'is_deleted': True,
        }

    def _get_deleted_id(self, resource_ids: dict[str, UUID]) -> UUID:
        return resource_ids['element_id']
