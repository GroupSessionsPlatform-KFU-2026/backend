from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query, Depends

from fastapi import Security
from src.app.dependencies.security import get_current_user
from src.app.models.user import User
from src.app.services.board_elements_comments import BoardElementCommentService
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
    room_id: UUID,
    element_id: UUID,
    filters: Annotated[BoardElementCommentFilters, Query()],
    comment_service: BoardElementCommentService = Depends(),
    current_user: User = Security(get_current_user, scopes=['board:read']),
) -> Sequence[BoardElementCommentPublic]:
    return await comment_service.get_comments(room_id, element_id, filters)


@router.post('/')
async def create_board_element_comment(
    room_id: UUID,
    element_id: UUID,
    comment_create: BoardElementCommentCreate,
    comment_service: BoardElementCommentService = Depends(),
    current_user: User = Security(get_current_user, scopes=['board:write']),
) -> Optional[BoardElementCommentPublic]:
    # TODO: author_id should come from the current authenticated
    #  user after OAuth2 is implemented.
    return await comment_service.create_comment(room_id, element_id, comment_create)


@router.put('/{comment_id}')
async def update_board_element_comment(
    room_id: UUID,
    element_id: UUID,
    comment_id: UUID,
    comment_update: BoardElementCommentUpdate,
    comment_service: BoardElementCommentService = Depends(),
    current_user: User = Security(get_current_user, scopes=['board:write']),
) -> Optional[BoardElementCommentPublic]:
    # TODO: validate comment ownership after OAuth2 is implemented.
    return await comment_service.update_comment(
        room_id,
        element_id,
        comment_id,
        comment_update,
    )


@router.delete('/{comment_id}')
async def delete_board_element_comment(
    room_id: UUID,
    element_id: UUID,
    comment_id: UUID,
    comment_service: BoardElementCommentService = Depends(),
    current_user: User = Security(get_current_user, scopes=['board:delete']),
) -> Optional[BoardElementCommentPublic]:
    # TODO: validate comment ownership after OAuth2 is implemented.
    return await comment_service.delete_comment(room_id, element_id, comment_id)
