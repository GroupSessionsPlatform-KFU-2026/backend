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
        filters: ChatMessageFilters,
    ) -> Sequence[ChatMessage]:
        return await self.__repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    async def create_message(
        self,
        message_create: ChatMessageCreate,
    ) -> ChatMessage:
        message_dump = message_create.model_dump()
        message = ChatMessage(
            **message_dump,
            sent_at=datetime.now(timezone.utc),
            is_edited=False,
        )
        # TODO: sender_id should come from OAuth current user later.
        return await self.__repository.save(message)

    async def get_message(self, message_id: UUID) -> Optional[ChatMessage]:
        return await self.__repository.get(message_id)

    async def update_message(
        self,
        message_update: ChatMessageUpdate,
        message_id: UUID,
    ) -> Optional[ChatMessage]:
        message = await self.__repository.get(message_id)
        if message is None:
            return None

        message.content = message_update.content
        message.is_edited = True
        return await self.__repository.save(message)

    async def delete_message(self, message_id: UUID) -> Optional[ChatMessage]:
        return await self.__repository.delete(message_id)
