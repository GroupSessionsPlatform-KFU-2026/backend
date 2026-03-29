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
    return await chat_service.get_messages(room_id, filters)


@router.post('/')
async def create_message(
    room_id: UUID,
    message_create: ChatMessageCreate,
    chat_service: ChatMessageServiceDep,
) -> ChatMessagePublic:
    # TODO: sender_id should come from the current authenticated
    #  user after OAuth2 is implemented.
    return await chat_service.create_message(room_id, message_create)


@router.put('/{message_id}')
async def update_message(
    room_id: UUID,
    message_id: UUID,
    message_update: ChatMessageUpdate,
    chat_service: ChatMessageServiceDep,
) -> Optional[ChatMessagePublic]:
    # TODO: validate message ownership inside the room after OAuth2 is implemented.
    return await chat_service.update_message(room_id, message_id, message_update)


@router.delete('/{message_id}')
async def delete_message(
    room_id: UUID,
    message_id: UUID,
    chat_service: ChatMessageServiceDep,
) -> Optional[ChatMessagePublic]:
    # TODO: validate message ownership inside the room after OAuth2 is implemented.
    return await chat_service.delete_message(room_id, message_id)
