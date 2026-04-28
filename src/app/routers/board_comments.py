from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.core.responses import auth_responses, detail_responses
from src.app.dependencies.room_access import require_comment_manage_access
from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import BoardElementCommentServiceDep
from src.app.models.board_element_comment import (
    BoardElementCommentCreate,
    BoardElementCommentPublic,
    BoardElementCommentUpdate,
)
from src.app.models.user import User as UserModel
from src.app.schemas.board_element_comment_filters import BoardElementCommentFilters
from src.app.schemas.pagination import PaginatedResponse, build_paginated_response
from src.app.utils.errors import NotFoundError

router = APIRouter(
    prefix='/rooms/{room_id}/board-elements/{element_id}/comments',
    tags=['board-comments'],
)


@router.get(
    '/',
    dependencies=[Security(require_scoped_user, scopes=['board:read'])],
    responses=auth_responses,
)
async def get_board_element_comments(
    room_id: UUID,
    element_id: UUID,
    filters: Annotated[BoardElementCommentFilters, Query()],
    comment_service: BoardElementCommentServiceDep,
) -> PaginatedResponse[BoardElementCommentPublic]:
    comments = await comment_service.get_comments(room_id, element_id, filters)
    total = await comment_service.count_comments(room_id, element_id, filters)

    return build_paginated_response(
        items=list(comments),
        total=total,
        offset=filters.offset,
        limit=filters.limit,
    )


@router.post(
    '/',
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def create_board_element_comment(
    room_id: UUID,
    element_id: UUID,
    comment_create: BoardElementCommentCreate,
    comment_service: BoardElementCommentServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['board:write']),
    ],
) -> BoardElementCommentPublic:
    comment_create = comment_create.model_copy(
        update={
            'board_element_id': element_id,
            'author_id': current_user.id,
        },
    )

    comment = await comment_service.create_comment(room_id, element_id, comment_create)

    if comment is None:
        raise NotFoundError

    return comment


@router.put(
    '/{comment_id}',
    dependencies=[
        Security(
            require_comment_manage_access,
            scopes=['board:write'],
        )
    ],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def update_board_element_comment(
    room_id: UUID,
    element_id: UUID,
    comment_id: UUID,
    comment_update: BoardElementCommentUpdate,
    comment_service: BoardElementCommentServiceDep,
) -> BoardElementCommentPublic:
    comment = await comment_service.update_comment(
        room_id,
        element_id,
        comment_id,
        comment_update,
    )

    if comment is None:
        raise NotFoundError()

    return comment


@router.delete(
    '/{comment_id}',
    dependencies=[
        Security(
            require_comment_manage_access,
            scopes=['board:delete'],
        )
    ],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def delete_board_element_comment(
    room_id: UUID,
    element_id: UUID,
    comment_id: UUID,
    comment_service: BoardElementCommentServiceDep,
) -> BoardElementCommentPublic:
    comment = await comment_service.delete_comment(room_id, element_id, comment_id)

    if comment is None:
        raise NotFoundError

    return comment
