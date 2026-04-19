from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.app.dependencies.security import (
    CurrentUserBoardDeleteDep,
    CurrentUserBoardReadDep,
    CurrentUserBoardWriteDep,
)
from src.app.dependencies.services import (
    BoardElementCommentServiceDep,
    RoomAccessServiceDep,
)
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


async def require_comment_write_access(
    room_id: UUID,
    element_id: UUID,
    comment_id: UUID,
    room_access: RoomAccessServiceDep,
    current_user: CurrentUserBoardWriteDep,
) -> None:
    await room_access.ensure_comment_manage(
        room_id,
        element_id,
        comment_id,
        current_user.id,
    )


async def require_comment_delete_access(
    room_id: UUID,
    element_id: UUID,
    comment_id: UUID,
    room_access: RoomAccessServiceDep,
    current_user: CurrentUserBoardDeleteDep,
) -> None:
    await room_access.ensure_comment_manage(
        room_id,
        element_id,
        comment_id,
        current_user.id,
    )


@router.get('/')
async def get_board_element_comments(
    room_id: UUID,
    element_id: UUID,
    filters: Annotated[BoardElementCommentFilters, Query()],
    comment_service: BoardElementCommentServiceDep,
    _current_user: CurrentUserBoardReadDep,
) -> Sequence[BoardElementCommentPublic]:
    return await comment_service.get_comments(room_id, element_id, filters)


@router.post('/')
async def create_board_element_comment(
    room_id: UUID,
    element_id: UUID,
    comment_create: BoardElementCommentCreate,
    comment_service: BoardElementCommentServiceDep,
    current_user: CurrentUserBoardWriteDep,
) -> Optional[BoardElementCommentPublic]:
    comment_create = comment_create.model_copy(
        update={
            'board_element_id': element_id,
            'author_id': current_user.id,
        }
    )
    return await comment_service.create_comment(room_id, element_id, comment_create)


@router.put(
    '/{comment_id}',
    dependencies=[Depends(require_comment_write_access)],
)
async def update_board_element_comment(
    room_id: UUID,
    element_id: UUID,
    comment_id: UUID,
    comment_update: BoardElementCommentUpdate,
    comment_service: BoardElementCommentServiceDep,
) -> Optional[BoardElementCommentPublic]:
    return await comment_service.update_comment(
        room_id,
        element_id,
        comment_id,
        comment_update,
    )


@router.delete(
    '/{comment_id}',
    dependencies=[Depends(require_comment_delete_access)],
)
async def delete_board_element_comment(
    room_id: UUID,
    element_id: UUID,
    comment_id: UUID,
    comment_service: BoardElementCommentServiceDep,
) -> Optional[BoardElementCommentPublic]:
    return await comment_service.delete_comment(room_id, element_id, comment_id)
