from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query

from src.app.dependencies.route_guards import (
    BoardReadGuard,
    CurrentUserBoardDeleteDep,
    CurrentUserBoardWriteDep,
)
from src.app.dependencies.router_bundles import (
    BoardCommentMutationDepsDep,
    RoomElementPathDep,
)
from src.app.dependencies.services import BoardElementCommentServiceDep
from src.app.models.board_element_comment import (
    BoardElementCommentCreate,
    BoardElementCommentPublic,
)
from src.app.schemas.board_element_comment_filters import BoardElementCommentFilters

router = APIRouter(
    prefix='/rooms/{room_id}/board-elements/{element_id}/comments',
    tags=['board-comments'],
)


@router.get('/', dependencies=[BoardReadGuard])
async def get_board_element_comments(
    path: RoomElementPathDep,
    filters: Annotated[BoardElementCommentFilters, Query()],
    comment_service: BoardElementCommentServiceDep,
) -> Sequence[BoardElementCommentPublic]:
    return await comment_service.get_comments(
        path.room_id,
        path.element_id,
        filters,
    )


@router.post('/')
async def create_board_element_comment(
    path: RoomElementPathDep,
    comment_create: BoardElementCommentCreate,
    comment_service: BoardElementCommentServiceDep,
    current_user: CurrentUserBoardWriteDep,
) -> Optional[BoardElementCommentPublic]:
    comment_create = comment_create.model_copy(
        update={
            'board_element_id': path.element_id,
            'author_id': current_user.id,
        }
    )
    return await comment_service.create_comment(
        path.room_id,
        path.element_id,
        comment_create,
    )


@router.delete('/{comment_id}')
async def delete_board_element_comment(
    path: RoomElementPathDep,
    comment_id: UUID,
    deps: BoardCommentMutationDepsDep,
    current_user: CurrentUserBoardDeleteDep,
) -> Optional[BoardElementCommentPublic]:
    await deps.room_access.ensure_comment_manage(
        room_id=path.room_id,
        element_id=path.element_id,
        comment_id=comment_id,
        user_id=current_user.id,
    )
    return await deps.comment_service.delete_comment(
        path.room_id,
        path.element_id,
        comment_id,
    )
