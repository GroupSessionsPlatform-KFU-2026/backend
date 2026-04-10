from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.core.responses import auth_responses, detail_responses
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
from src.app.schemas.pagination import PaginatedResponse, build_paginated_response
from src.app.utils.errors import NotFoundError

router = APIRouter(
    prefix='/rooms/{room_id}/messages',
    tags=['chat'],
)


@router.get(
    '/',
    dependencies=[Security(require_scoped_user, scopes=['chat:read'])],
    responses=auth_responses,
)
async def get_room_messages(
    room_id: UUID,
    filters: Annotated[ChatMessageFilters, Query()],
    chat_service: ChatMessageServiceDep,
) -> PaginatedResponse[ChatMessagePublic]:
    messages = await chat_service.get_messages(room_id, filters)
    total = await chat_service.count_messages(room_id, filters)

    return build_paginated_response(
        items=list(messages),
        total=total,
        offset=filters.offset,
        limit=filters.limit,
    )


@router.post(
    '/',
    responses=auth_responses,
)
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
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def update_message(
    room_id: UUID,
    message_id: UUID,
    message_update: ChatMessageUpdate,
    chat_service: ChatMessageServiceDep,
) -> ChatMessagePublic:
    message = await chat_service.update_message(room_id, message_id, message_update)

    if message is None:
        raise NotFoundError

    return message


@router.delete(
    '/{message_id}',
    dependencies=[
        Security(
            require_message_manage_access,
            scopes=['chat:delete'],
        )
    ],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def delete_message(
    room_id: UUID,
    message_id: UUID,
    chat_service: ChatMessageServiceDep,
) -> ChatMessagePublic:
    message = await chat_service.delete_message(room_id, message_id)

    if message is None:
        raise NotFoundError

    return message