from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from src.app.dependencies.repositories import (
    ChatMessageRepository,
    ChatMessageRepositoryDep,
)

from src.app.models.chat_message import (
    ChatMessage,
    ChatMessageCreate,
)

from src.app.schemas.chat_message_filters import ChatMessageFilters

class ChatMessageService:
    __repository: ChatMessageRepository

    def __init__(self, chat_repository: ChatMessageRepositoryDep):
        self.__chat_repository = chat_repository

    async def get_message(self, filters: ChatMessageFilters) -> Sequence[ChatMessage]:
        return await self.__chat_repository.fetch(
            filters = filters,
            offset = filters.offset,
            limit = filters.limit,
        )
    
    async def create_message(self, message_create: ChatMessageCreate) -> ChatMessage:
        message_dump = message_create.model_dump()
        message = ChatMessage(
            **message_dump,
            sent_at=datetime.utcnow(),
            is_edited=False,
        )
        return await self.__repository.save(message)

    async def update_message(
        self, message_update: ChatMessageUpdate, message_id: UUID
    ) -> Optional[ChatMessage]:
        message = await self.__repository.get(message_id)
        if message is None:
            return None

        message.content = message_update.content
        message.is_edited = True

        return await self.__repository.save(message)

    async def delete_message(self, message_id: UUID) -> Optional[ChatMessage]:
        return await self.__repository.delete(message_id)