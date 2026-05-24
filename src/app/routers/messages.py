from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.core.responses import auth_responses, detail_responses
from src.app.dependencies.room_access import (
    require_message_manage_access,
    require_room_access,
)
from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import ChatMessageServiceDep
from src.app.models.chat_message import (
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatMessageWithSender,
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
    dependencies=[Security(require_room_access, scopes=['chat:read'])],
    responses=auth_responses,
)
async def get_room_messages(
    room_id: UUID,
    filters: Annotated[ChatMessageFilters, Query()],
    chat_service: ChatMessageServiceDep,
) -> PaginatedResponse[ChatMessageWithSender]:
    messages = await chat_service.get_messages(room_id, filters)
    total = await chat_service.count_messages(room_id, filters)

    return build_paginated_response(
        items=await chat_service.to_public_list(messages),
        total=total,
        offset=filters.offset,
        limit=filters.limit,
    )


@router.post(
    '/',
    dependencies=[Security(require_room_access, scopes=['chat:write'])],
    responses=auth_responses,
)
async def create_message(
    room_id: UUID,
    message_create: ChatMessageCreate,
    chat_service: ChatMessageServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=[]),
    ],
) -> ChatMessageWithSender:
    message_create = message_create.model_copy(
        update={
            'room_id': room_id,
            'sender_id': current_user.id,
        }
    )
    message = await chat_service.create_message(room_id, message_create)
    return await chat_service.to_public(message)


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
) -> ChatMessageWithSender:
    message = await chat_service.update_message(room_id, message_id, message_update)

    if message is None:
        raise NotFoundError()

    return await chat_service.to_public(message)


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
) -> ChatMessageWithSender:
    message = await chat_service.delete_message(room_id, message_id)

    if message is None:
        raise NotFoundError()

    return await chat_service.to_public(message)
