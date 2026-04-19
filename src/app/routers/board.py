from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.app.dependencies.security import (
    CurrentUserBoardDeleteDep,
    CurrentUserBoardReadDep,
    CurrentUserBoardWriteDep,
)
from src.app.dependencies.services import (
    BoardElementServiceDep,
    RoomAccessServiceDep,
)
from src.app.models.board_element import (
    BoardElementCreate,
    BoardElementPublic,
    BoardElementUpdate,
)
from src.app.schemas.board_elements_filters import BoardElementFilters

router = APIRouter(
    prefix='/rooms/{room_id}/board-elements',
    tags=['board'],
)


async def require_board_element_write_access(
    room_id: UUID,
    element_id: UUID,
    room_access: RoomAccessServiceDep,
    current_user: CurrentUserBoardWriteDep,
) -> None:
    await room_access.ensure_board_element_manage(
        room_id,
        element_id,
        current_user.id,
    )


async def require_board_element_delete_access(
    room_id: UUID,
    element_id: UUID,
    room_access: RoomAccessServiceDep,
    current_user: CurrentUserBoardDeleteDep,
) -> None:
    await room_access.ensure_board_element_manage(
        room_id,
        element_id,
        current_user.id,
    )


@router.get('/')
async def get_board_elements(
    room_id: UUID,
    filters: Annotated[BoardElementFilters, Query()],
    board_service: BoardElementServiceDep,
    _current_user: CurrentUserBoardReadDep,
) -> Sequence[BoardElementPublic]:
    return await board_service.get_elements(room_id, filters)


@router.post('/')
async def create_board_element(
    room_id: UUID,
    element_create: BoardElementCreate,
    board_service: BoardElementServiceDep,
    current_user: CurrentUserBoardWriteDep,
) -> BoardElementPublic:
    element_create = element_create.model_copy(
        update={
            'room_id': room_id,
            'author_id': current_user.id,
        }
    )
    return await board_service.create_element(room_id, element_create)


@router.put(
    '/{element_id}',
    dependencies=[Depends(require_board_element_write_access)],
)
async def update_board_element(
    room_id: UUID,
    element_id: UUID,
    element_update: BoardElementUpdate,
    board_service: BoardElementServiceDep,
) -> Optional[BoardElementPublic]:
    return await board_service.update_element(room_id, element_id, element_update)


@router.delete(
    '/{element_id}',
    dependencies=[Depends(require_board_element_delete_access)],
)
async def delete_board_element(
    room_id: UUID,
    element_id: UUID,
    board_service: BoardElementServiceDep,
) -> Optional[BoardElementPublic]:
    return await board_service.delete_element(room_id, element_id)
