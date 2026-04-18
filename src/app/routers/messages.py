from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query

from src.app.dependencies.route_guards import (
    ChatReadGuard,
    CurrentChatDeleteUserDep,
    CurrentChatWriteUserDep,
)
from src.app.dependencies.router_bundles import MessageMutationDepsDep
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


@router.get('/', dependencies=[ChatReadGuard])
async def get_room_messages(
    room_id: UUID,
    filters: Annotated[ChatMessageFilters, Query()],
    chat_service: ChatMessageServiceDep,
) -> Sequence[ChatMessagePublic]:
    return await chat_service.get_messages(room_id, filters)


@router.post('/')
async def create_message(
    room_id: UUID,
    message_create: ChatMessageCreate,
    chat_service: ChatMessageServiceDep,
    current_user: CurrentChatWriteUserDep,
) -> ChatMessagePublic:
    message_create = message_create.model_copy(
        update={
            'room_id': room_id,
            'sender_id': current_user.id,
        }
    )
    return await chat_service.create_message(room_id, message_create)


@router.put('/{message_id}')
async def update_message(
    room_id: UUID,
    message_id: UUID,
    message_update: ChatMessageUpdate,
    deps: MessageMutationDepsDep,
    current_user: CurrentChatWriteUserDep,
) -> Optional[ChatMessagePublic]:
    await deps.room_access.ensure_message_manage(
        room_id=room_id,
        message_id=message_id,
        user_id=current_user.id,
    )
    return await deps.chat_service.update_message(room_id, message_id, message_update)


@router.delete('/{message_id}')
async def delete_message(
    room_id: UUID,
    message_id: UUID,
    deps: MessageMutationDepsDep,
    current_user: CurrentChatDeleteUserDep,
) -> Optional[ChatMessagePublic]:
    await deps.room_access.ensure_message_manage(
        room_id=room_id,
        message_id=message_id,
        user_id=current_user.id,
    )
    return await deps.chat_service.delete_message(room_id, message_id)
