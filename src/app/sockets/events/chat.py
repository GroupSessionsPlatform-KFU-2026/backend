from typing import Any
from uuid import UUID

from src.app.models.chat_message import (
    ChatMessage,
    ChatMessageCreate,
    ChatMessageUpdate,
)
from src.app.services.chat_messages import ChatMessageService
from src.app.sockets.events.base_room_crud import BaseRoomCrudSocketHandler
from src.app.sockets.events.common import (
    SocketIdentity,
    parse_uuid,
    require_non_empty_string,
)
from src.app.sockets.events.contexts import socket_service_factory
from src.app.sockets.manager import SocketConnectionManager


class ChatEventError(Exception):
    pass


class ChatSocketEventHandler(
    BaseRoomCrudSocketHandler[ChatMessageService, ChatMessageCreate, ChatMessageUpdate]
):
    _create_command = 'chat.send'
    _update_command = 'chat.update'
    _delete_command = 'chat.delete'

    _write_scope = 'chat:write'
    _delete_scope = 'chat:delete'

    _created_event = 'chat.message.created'
    _updated_event = 'chat.message.updated'
    _deleted_event = 'chat.message.deleted'

    _resource_response_key = 'message'
    _deleted_response_key = 'deleted_message_id'

    _create_target_not_found_message = 'Room not found'
    _resource_not_found_message = 'Message not found'
    _update_forbidden_message = 'You cannot edit this message'
    _delete_forbidden_message = 'You cannot delete this message'

    def __init__(self, socket_manager: SocketConnectionManager) -> None:
        super().__init__(
            socket_manager=socket_manager,
            context_factory=socket_service_factory.chat,
            error_cls=ChatEventError,
        )

    def _parse_create_payload(
        self,
        payload: dict[str, Any],
        identity: SocketIdentity,
    ) -> ChatMessageCreate:
        content = require_non_empty_string(
            payload.get('content'),
            'content',
            ChatEventError,
        )
        return ChatMessageCreate(
            room_id=identity.room_id,
            sender_id=identity.user_id,
            content=content,
        )

    def _parse_update_payload(
        self,
        payload: dict[str, Any],
    ) -> tuple[dict[str, UUID], ChatMessageUpdate]:
        message_id = parse_uuid(
            payload.get('message_id'),
            'message id',
            ChatEventError,
        )
        content = require_non_empty_string(
            payload.get('content'),
            'content',
            ChatEventError,
        )
        return {'message_id': message_id}, ChatMessageUpdate(content=content)

    def _parse_delete_payload(
        self,
        payload: dict[str, Any],
    ) -> dict[str, UUID]:
        message_id = parse_uuid(
            payload.get('message_id'),
            'message id',
            ChatEventError,
        )
        return {'message_id': message_id}

    async def _create_resource(
        self,
        service: ChatMessageService,
        identity: SocketIdentity,
        payload: ChatMessageCreate,
    ) -> ChatMessage | None:
        return await service.create_message(
            room_id=identity.room_id,
            message_create=payload,
        )

    async def _get_existing_resource(
        self,
        service: ChatMessageService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> ChatMessage | None:
        return await service.get_message_in_room(
            room_id=identity.room_id,
            message_id=resource_ids['message_id'],
        )

    async def _update_resource(
        self,
        service: ChatMessageService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
        payload: ChatMessageUpdate,
    ) -> ChatMessage | None:
        return await service.update_message(
            room_id=identity.room_id,
            message_id=resource_ids['message_id'],
            message_update=payload,
        )

    async def _delete_resource(
        self,
        service: ChatMessageService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> ChatMessage | None:
        return await service.delete_message(
            room_id=identity.room_id,
            message_id=resource_ids['message_id'],
        )

    def _get_author_id(self, resource: ChatMessage) -> UUID:
        return resource.sender_id

    def _build_deleted_event_payload(
        self,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> dict[str, Any]:
        return {
            'id': str(resource_ids['message_id']),
            'room_id': str(identity.room_id),
        }

    def _get_deleted_id(self, resource_ids: dict[str, UUID]) -> UUID:
        return resource_ids['message_id']
