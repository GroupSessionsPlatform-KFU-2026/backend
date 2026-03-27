from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query

from src.app.dependencies.services import BoardElementCommentServiceDep
from src.app.models.board_element_comment import (
    BoardElementCommentCreate,
    BoardElementCommentPublic,
    BoardElementCommentUpdate,
)
from src.app.schemas.board_element_comment_filters import BoardElementCommentFilters

router = APIRouter(
    prefix='/rooms/{room_id}/board-elements/{element_id}/comments',
    tags=['board-comments'],
)


@router.get('/')
async def get_board_element_comments(
    # room_id: UUID,
    element_id: UUID,
    comment_service: BoardElementCommentServiceDep,
    filters: Annotated[BoardElementCommentFilters, Query()],
) -> Sequence[BoardElementCommentPublic]:
    filters.board_element_id = element_id
    return await comment_service.get_comments(filters)


@router.post('/')
async def create_board_element_comment(
    # room_id: UUID,
    element_id: UUID,
    comment_create: BoardElementCommentCreate,
    comment_service: BoardElementCommentServiceDep,
) -> BoardElementCommentPublic:
    payload = comment_create.model_copy(update={'board_element_id': element_id})
    # TODO: author_id should come from OAuth current user later.
    return await comment_service.create_comment(payload)


@router.put('/{comment_id}')
async def update_board_element_comment(
    # room_id: UUID,
    # element_id: UUID,
    comment_id: UUID,
    comment_update: BoardElementCommentUpdate,
    comment_service: BoardElementCommentServiceDep,
) -> Optional[BoardElementCommentPublic]:
    # TODO: validate ownership after auth is implemented.
    return await comment_service.update_comment(comment_update, comment_id)


@router.delete('/{comment_id}')
async def delete_board_element_comment(
    # room_id: UUID,
    # element_id: UUID,
    comment_id: UUID,
    comment_service: BoardElementCommentServiceDep,
) -> Optional[BoardElementCommentPublic]:
    # TODO: validate ownership after auth is implemented.
    return await comment_service.delete_comment(comment_id)
