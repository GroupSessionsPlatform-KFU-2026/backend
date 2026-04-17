from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query

from src.app.dependencies.security import (
    CurrentUserChatDeleteDep,
    CurrentUserChatReadDep,
    CurrentUserChatWriteDep,
)
from src.app.dependencies.services import ChatMessageServiceDep, RoomAccessServiceDep
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
    filters: Annotated[ChatMessageFilters, Query()],
    chat_service: ChatMessageServiceDep,
    _current_user: CurrentUserChatReadDep,
) -> Sequence[ChatMessagePublic]:
    return await chat_service.get_messages(room_id, filters)


@router.post('/')
async def create_message(
    room_id: UUID,
    message_create: ChatMessageCreate,
    chat_service: ChatMessageServiceDep,
    current_user: CurrentUserChatWriteDep,
) -> ChatMessagePublic:
    message_create = message_create.model_copy(
        update={
            'room_id': room_id,
            'sender_id': current_user.id,
        }
    )
    return await chat_service.create_message(room_id, message_create)


@router.put('/{message_id}')
async def update_message(  # noqa: PLR0913
    room_id: UUID,
    message_id: UUID,
    message_update: ChatMessageUpdate,
    chat_service: ChatMessageServiceDep,
    room_access: RoomAccessServiceDep,
    current_user: CurrentUserChatWriteDep,
) -> Optional[ChatMessagePublic]:
    await room_access.ensure_message_owner(room_id, message_id, current_user.id)
    return await chat_service.update_message(room_id, message_id, message_update)


@router.delete('/{message_id}')
async def delete_message(
    room_id: UUID,
    message_id: UUID,
    chat_service: ChatMessageServiceDep,
    room_access: RoomAccessServiceDep,
    current_user: CurrentUserChatDeleteDep,
) -> Optional[ChatMessagePublic]:
    await room_access.ensure_message_owner(room_id, message_id, current_user.id)
    return await chat_service.delete_message(room_id, message_id)
