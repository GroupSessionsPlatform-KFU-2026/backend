from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query

from src.app.dependencies.services import ChatMessageServiceDep
from src.app.models.chat_message import (
    ChatMessageCreate,
    ChatMessagePublic,
    ChatMessageUpdate,
)
from src.app.schemas.chat_message_filters import ChatMessageFilters

router = APIRouter(
    prefix='/rooms/{room_id}/messages',
    tags=['chat'],
)


@router.get('/')
async def get_room_messages(
    room_id: UUID,
    chat_service: ChatMessageServiceDep,
    filters: Annotated[ChatMessageFilters, Query()],
) -> Sequence[ChatMessagePublic]:
    filters.room_id = room_id
    return await chat_service.get_messages(filters)


@router.post('/')
async def create_message(
    room_id: UUID,
    message_create: ChatMessageCreate,
    chat_service: ChatMessageServiceDep,
) -> ChatMessagePublic:
    payload = message_create.model_copy(update={'room_id': room_id})
    # TODO: sender_id should come from OAuth current user later.
    return await chat_service.create_message(payload)


@router.put('/{message_id}')
async def update_message(
    # room_id: UUID,
    message_id: UUID,
    message_update: ChatMessageUpdate,
    chat_service: ChatMessageServiceDep,
) -> Optional[ChatMessagePublic]:
    # TODO: validate message ownership after auth is implemented.
    return await chat_service.update_message(message_update, message_id)


@router.delete('/{message_id}')
async def delete_message(
    # room_id: UUID,
    message_id: UUID,
    chat_service: ChatMessageServiceDep,
) -> Optional[ChatMessagePublic]:
    # TODO: validate message ownership after auth is implemented.
    return await chat_service.delete_message(message_id)
