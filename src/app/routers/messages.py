from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.dependencies.room_access import require_message_manage_access
from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import ChatMessageServiceDep
from src.app.models.chat_message import (
    ChatMessageCreate,
    ChatMessagePublic,
    ChatMessageUpdate,
)
from src.app.models.user import User as UserModel
from src.app.schemas.chat_message_filters import ChatMessageFilters

router = APIRouter(
    prefix='/rooms/{room_id}/messages',
    tags=['chat'],
)


@router.get(
    '/',
    dependencies=[Security(require_scoped_user, scopes=['chat:read'])],
)
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
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['chat:write']),
    ],
) -> ChatMessagePublic:
    message_create = message_create.model_copy(
        update={
            'room_id': room_id,
            'sender_id': current_user.id,
        }
    )
    return await chat_service.create_message(room_id, message_create)


@router.put(
    '/{message_id}',
    dependencies=[
        Security(
            require_message_manage_access,
            scopes=['chat:write'],
        )
    ],
)
async def update_message(
    room_id: UUID,
    message_id: UUID,
    message_update: ChatMessageUpdate,
    chat_service: ChatMessageServiceDep,
) -> Optional[ChatMessagePublic]:
    return await chat_service.update_message(room_id, message_id, message_update)


@router.delete(
    '/{message_id}',
    dependencies=[
        Security(
            require_message_manage_access,
            scopes=['chat:delete'],
        )
    ],
)
async def delete_message(
    room_id: UUID,
    message_id: UUID,
    chat_service: ChatMessageServiceDep,
) -> Optional[ChatMessagePublic]:
    return await chat_service.delete_message(room_id, message_id)
