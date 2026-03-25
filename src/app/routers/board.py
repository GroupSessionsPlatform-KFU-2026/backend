from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query

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


@router.get('/')
async def get_board_elements(
    room_id: UUID,
    board_service: BoardElementServiceDep,
    filters: Annotated[BoardElementFilters, Query()],
) -> Sequence[BoardElementPublic]:
    filters.room_id = room_id
    return await board_service.get_elements(filters)


@router.post('/')
async def create_board_element(
    room_id: UUID,
    element_create: BoardElementCreate,
    board_service: BoardElementServiceDep,
) -> BoardElementPublic:
    payload = element_create.model_copy(update={'room_id': room_id})
    # TODO: author_id should come from OAuth current user later.
    return await board_service.create_element(payload)


@router.get('/{element_id}')
async def get_board_element(
    room_id: UUID,
    element_id: UUID,
    board_service: BoardElementServiceDep,
) -> Optional[BoardElementPublic]:
    filters = BoardElementFilters(room_id=room_id, offset=0, limit=100)
    elements = await board_service.get_elements(filters)
    for element in elements:
        if element.id == element_id:
            return element
    return None


@router.put('/{element_id}')
async def update_board_element(
    # room_id: UUID,
    element_id: UUID,
    element_update: BoardElementUpdate,
    board_service: BoardElementServiceDep,
) -> Optional[BoardElementPublic]:
    # TODO: validate ownership after auth is implemented.
    return await board_service.update_element(element_update, element_id)


@router.delete('/{element_id}')
async def delete_board_element(
    # room_id: UUID,
    element_id: UUID,
    board_service: BoardElementServiceDep,
) -> Optional[BoardElementPublic]:
    # TODO: validate ownership after auth is implemented.
    return await board_service.delete_element(element_id)
