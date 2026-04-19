from typing import Any
from uuid import UUID

import socketio

from src.app.models.chat_message import ChatMessageCreate, ChatMessageUpdate
from src.app.services.chat_messages import ChatMessageService
from src.app.sockets.events.base_room_crud import BaseRoomCrudSocketHandler
from src.app.sockets.events.common import (
    SocketIdentity,
    parse_uuid,
    register_event_handlers,
    require_non_empty_string,
)
from src.app.sockets.events.contexts import socket_service_factory
from src.app.sockets.manager import SocketConnectionManager


class ChatEventError(Exception):
    pass


class ChatSocketHandler(
    BaseRoomCrudSocketHandler[ChatMessageService, ChatMessageCreate, ChatMessageUpdate]
):
    write_scope = 'chat:write'
    delete_scope = 'chat:delete'

    created_event = 'chat.message.created'
    updated_event = 'chat.message.updated'
    deleted_event = 'chat.message.deleted'

    resource_response_key = 'message'
    deleted_response_key = 'deleted_message_id'

    create_target_not_found_message = 'Message not found'
    resource_not_found_message = 'Message not found'
    update_forbidden_message = 'You cannot edit this message'
    delete_forbidden_message = 'You cannot delete this message'

    def parse_create_payload(
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

    def parse_update_payload(
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

    def parse_delete_payload(
        self,
        payload: dict[str, Any],
    ) -> dict[str, UUID]:
        message_id = parse_uuid(
            payload.get('message_id'),
            'message id',
            ChatEventError,
        )
        return {'message_id': message_id}

    async def create_resource(
        self,
        service: ChatMessageService,
        identity: SocketIdentity,
        payload: ChatMessageCreate,
    ):
        return await service.create_message(
            room_id=identity.room_id,
            message_create=payload,
        )

    async def get_existing_resource(
        self,
        service: ChatMessageService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ):
        return await service.get_message_in_room(
            room_id=identity.room_id,
            message_id=resource_ids['message_id'],
        )

    async def update_resource(
        self,
        service: ChatMessageService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
        payload: ChatMessageUpdate,
    ):
        return await service.update_message(
            room_id=identity.room_id,
            message_id=resource_ids['message_id'],
            message_update=payload,
        )

    async def delete_resource(
        self,
        service: ChatMessageService,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ):
        return await service.delete_message(
            room_id=identity.room_id,
            message_id=resource_ids['message_id'],
        )

    def get_author_id(self, resource) -> UUID:
        return resource.sender_id

    def build_deleted_event_payload(
        self,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> dict[str, Any]:
        return {
            'id': str(resource_ids['message_id']),
            'room_id': str(identity.room_id),
        }

    def get_deleted_id(self, resource_ids: dict[str, UUID]) -> UUID:
        return resource_ids['message_id']


def register_chat_events(
    sio: socketio.AsyncServer,
    socket_manager: SocketConnectionManager,
) -> None:
    handler = ChatSocketHandler(
        socket_manager=socket_manager,
        context_factory=socket_service_factory.chat,
        error_cls=ChatEventError,
    )

    register_event_handlers(
        sio=sio,
        socket_manager=socket_manager,
        handlers={
            'chat.send': handler.handle_create,
            'chat.update': handler.handle_update,
            'chat.delete': handler.handle_delete,
        },
        error_cls=ChatEventError,
    )
