from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query

from src.app.dependencies.route_guards import (
    BoardReadGuard,
    CurrentUserBoardDeleteDep,
    CurrentUserBoardWriteDep,
)
from src.app.dependencies.router_bundles import BoardMutationDepsDep
from src.app.dependencies.services import BoardElementServiceDep
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


@router.get('/', dependencies=[BoardReadGuard])
async def get_board_elements(
    room_id: UUID,
    filters: Annotated[BoardElementFilters, Query()],
    board_service: BoardElementServiceDep,
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


@router.put('/{element_id}')
async def update_board_element(
    room_id: UUID,
    element_id: UUID,
    element_update: BoardElementUpdate,
    deps: BoardMutationDepsDep,
    current_user: CurrentUserBoardWriteDep,
) -> Optional[BoardElementPublic]:
    await deps.room_access.ensure_board_element_manage(
        room_id=room_id,
        element_id=element_id,
        user_id=current_user.id,
    )
    return await deps.board_service.update_element(
        room_id,
        element_id,
        element_update,
    )


@router.delete('/{element_id}')
async def delete_board_element(
    room_id: UUID,
    element_id: UUID,
    deps: BoardMutationDepsDep,
    current_user: CurrentUserBoardDeleteDep,
) -> Optional[BoardElementPublic]:
    await deps.room_access.ensure_board_element_manage(
        room_id=room_id,
        element_id=element_id,
        user_id=current_user.id,
    )
    return await deps.board_service.delete_element(room_id, element_id)
