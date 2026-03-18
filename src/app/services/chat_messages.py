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
        return await self.__repository.fetch(
            filters=filters,
            extra_filters={'room_id': room_id},
            offset=filters.offset,
            limit=filters.limit,
        )

    async def create_message(
        self,
        room_id: UUID,
        message_create: ChatMessageCreate,
    ) -> ChatMessage:
        message_dump = message_create.model_dump(exclude={'room_id'})

        message = ChatMessage(
            **message_dump,
            room_id=room_id,
            created_at=datetime.now(timezone.utc),
            is_edited=False,
        )

        return await self.__repository.save(message)

    async def get_message_in_room(
        self,
        room_id: UUID,
        message_id: UUID,
    ) -> Optional[ChatMessage]:
        messages = await self.__repository.fetch(
            extra_filters={
                'id': message_id,
                'room_id': room_id,
            },
            limit=1,
        )
        return messages[0] if messages else None

    async def update_message(
        self,
        room_id: UUID,
        message_id: UUID,
        message_update: ChatMessageUpdate,
    ) -> Optional[ChatMessage]:
        message = await self.get_message_in_room(room_id, message_id)
        if message is None:
            return None

        message.content = message_update.content
        message.is_edited = True
        return await self.__repository.save(message)

    async def delete_message(
        self,
        room_id: UUID,
        message_id: UUID,
    ) -> Optional[ChatMessage]:
        message = await self.get_message_in_room(room_id, message_id)
        if message is None:
            return None
        return await self.__repository.delete(message.id)
    
    async def count_messages(
        self,
        room_id: UUID,
        filters: ChatMessageFilters,
    ) -> int:
        return await self.__repository.count(
            filters=filters,
            extra_filters={'room_id': room_id},
        )
