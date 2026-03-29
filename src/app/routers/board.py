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
    return await board_service.get_elements(room_id, filters)


@router.post('/')
async def create_board_element(
    room_id: UUID,
    element_create: BoardElementCreate,
    board_service: BoardElementServiceDep,
) -> BoardElementPublic:
    # TODO: author_id should come from the current authenticated
    #  user after OAuth2 is implemented.
    return await board_service.create_element(room_id, element_create)


@router.get('/{element_id}')
async def get_board_element(
    room_id: UUID,
    element_id: UUID,
    board_service: BoardElementServiceDep,
) -> Optional[BoardElementPublic]:
    return await board_service.get_element_in_room(room_id, element_id)


@router.put('/{element_id}')
async def update_board_element(
    room_id: UUID,
    element_id: UUID,
    element_update: BoardElementUpdate,
    board_service: BoardElementServiceDep,
) -> Optional[BoardElementPublic]:
    # TODO: validate room-scoped ownership after OAuth2 is implemented.
    return await board_service.update_element(room_id, element_id, element_update)


@router.delete('/{element_id}')
async def delete_board_element(
    room_id: UUID,
    element_id: UUID,
    board_service: BoardElementServiceDep,
) -> Optional[BoardElementPublic]:
    # TODO: validate room-scoped ownership after OAuth2 is implemented.
    return await board_service.delete_element(room_id, element_id)
