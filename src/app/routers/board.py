from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.core.responses import auth_responses, detail_responses
from src.app.dependencies.room_access import (
    require_board_element_manage_access,
    require_room_access,
    require_room_moderation_access,
)
from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import BoardElementServiceDep
from src.app.models.board_element import (
    BoardClearResponse,
    BoardElementCreate,
    BoardElementPublic,
    BoardElementUpdate,
)
from src.app.models.user import User as UserModel
from src.app.schemas.board_elements_filters import BoardElementFilters
from src.app.schemas.pagination import PaginatedResponse, build_paginated_response
from src.app.utils.errors import NotFoundError

router = APIRouter(
    prefix='/rooms/{room_id}/board-elements',
    tags=['board'],
)


@router.get(
    '/',
    dependencies=[Security(require_room_access, scopes=['board:read'])],
    responses=auth_responses,
)
async def get_board_elements(
    room_id: UUID,
    filters: Annotated[BoardElementFilters, Query()],
    board_service: BoardElementServiceDep,
) -> PaginatedResponse[BoardElementPublic]:
    elements = await board_service.get_elements(room_id, filters)
    total = await board_service.count_elements(room_id, filters)

    return build_paginated_response(
        items=board_service.to_public_list(elements),
        total=total,
        offset=filters.offset,
        limit=filters.limit,
    )


@router.post(
    '/',
    dependencies=[Security(require_room_access, scopes=['board:write'])],
    responses=auth_responses,
)
async def create_board_element(
    room_id: UUID,
    element_create: BoardElementCreate,
    board_service: BoardElementServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=[]),
    ],
) -> BoardElementPublic:
    element_create = element_create.model_copy(
        update={
            'room_id': room_id,
            'author_id': current_user.id,
        },
    )
    element = await board_service.create_element(room_id, element_create)
    return board_service.to_public(element)


@router.put(
    '/{element_id}',
    dependencies=[
        Security(
            require_board_element_manage_access,
            scopes=['board:write'],
        )
    ],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def update_board_element(
    room_id: UUID,
    element_id: UUID,
    element_update: BoardElementUpdate,
    board_service: BoardElementServiceDep,
) -> BoardElementPublic:
    element = await board_service.update_element(room_id, element_id, element_update)

    if element is None:
        raise NotFoundError()

    return board_service.to_public(element)


@router.delete(
    '/',
    dependencies=[
        Security(
            require_room_moderation_access,
            scopes=['board:delete'],
        )
    ],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def clear_board_elements(
    room_id: UUID,
    board_service: BoardElementServiceDep,
) -> BoardClearResponse:
    deleted_count = await board_service.clear_room_elements(room_id)
    return BoardClearResponse(room_id=room_id, deleted_count=deleted_count)


@router.delete(
    '/{element_id}',
    dependencies=[
        Security(
            require_board_element_manage_access,
            scopes=['board:delete'],
        )
    ],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def delete_board_element(
    room_id: UUID,
    element_id: UUID,
    board_service: BoardElementServiceDep,
) -> BoardElementPublic:
    element = await board_service.delete_element(room_id, element_id)

    if element is None:
        raise NotFoundError()

    return board_service.to_public(element)
