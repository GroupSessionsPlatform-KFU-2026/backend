from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from src.app.dependencies.repositories import (
    ChatMessageRepository,
    ChatMessageRepositoryDep,
)
from src.app.models.chat_message import (
    ChatMessage,
    ChatMessageCreate,
    ChatMessageUpdate,
)
from src.app.schemas.chat_message_filters import ChatMessageFilters


class ChatMessageService:
    __repository: ChatMessageRepository

    def __init__(self, repository: ChatMessageRepositoryDep):
        self.__repository = repository

    async def get_messages(
        self,
        room_id: UUID,
        filters: ChatMessageFilters,
    ) -> Sequence[ChatMessage]:
        repository_filters = ChatMessageFilters(
            sender_id=filters.sender_id,
            offset=filters.offset,
            limit=filters.limit,
        )
        messages = await self.__repository.fetch(
            filters=repository_filters,
            offset=repository_filters.offset,
            limit=repository_filters.limit,
        )
        return [message for message in messages if message.room_id == room_id]

    async def create_message(
        self,
        room_id: UUID,
        message_create: ChatMessageCreate,
    ) -> ChatMessage:
        message_dump = message_create.model_dump()
        message = ChatMessage(
            **message_dump,
            room_id=room_id,
            sent_at=datetime.now(timezone.utc),
            is_edited=False,
        )
        # TODO: sender_id should come from the current authenticated user
        #  after OAuth2 is implemented.
        return await self.__repository.save(message)

    async def get_message_in_room(
        self,
        room_id: UUID,
        message_id: UUID,
    ) -> Optional[ChatMessage]:
        message = await self.__repository.get(message_id)
        if message is None:
            return None
        if message.room_id != room_id:
            return None
        return message

    async def update_message(
        self,
        room_id: UUID,
        message_id: UUID,
        message_update: ChatMessageUpdate,
    ) -> Optional[ChatMessage]:
        message = await self.__repository.get(message_id)
        if message is None:
            return None
        if message.room_id != room_id:
            return None

        message.content = message_update.content
        message.is_edited = True
        return await self.__repository.save(message)

    async def delete_message(
        self,
        room_id: UUID,
        message_id: UUID,
    ) -> Optional[ChatMessage]:
        message = await self.__repository.get(message_id)
        if message is None:
            return None
        if message.room_id != room_id:
            return None
        return await self.__repository.delete(message_id)
