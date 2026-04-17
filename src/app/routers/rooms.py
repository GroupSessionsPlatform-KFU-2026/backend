from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query

from src.app.dependencies.security import (
    CurrentUserRoomsDeleteDep,
    CurrentUserRoomsReadDep,
    CurrentUserRoomsWriteDep,
)
from src.app.dependencies.services import RoomServiceDep
from src.app.models.room import RoomCreate, RoomPublic, RoomUpdate
from src.app.schemas.room_filters import RoomFilters
from src.app.schemas.room_request import JoinRoomRequest

router = APIRouter(
    prefix='/rooms',
    tags=['rooms'],
)


@router.get('/')
async def get_rooms(
    filters: Annotated[RoomFilters, Query()],
    room_service: RoomServiceDep,
    _current_user: CurrentUserRoomsReadDep,
) -> Sequence[RoomPublic]:
    return await room_service.get_rooms(filters)


@router.post('/')
async def create_room(
    room_create: RoomCreate,
    room_service: RoomServiceDep,
    current_user: CurrentUserRoomsWriteDep,
) -> RoomPublic:
    return await room_service.create_room(room_create, current_user.id)


@router.post('/join')
async def join_room(
    payload: JoinRoomRequest,
    room_service: RoomServiceDep,
    current_user: CurrentUserRoomsWriteDep,
):
    return await room_service.join_room(payload, current_user.id)


@router.put('/{room_id}')
async def update_room(
    room_update: RoomUpdate,
    room_id: UUID,
    room_service: RoomServiceDep,
    current_user: CurrentUserRoomsWriteDep,
) -> Optional[RoomPublic]:
    return await room_service.update_room(room_update, room_id, current_user.id)


@router.delete('/{room_id}')
async def end_room(
    room_id: UUID, room_service: RoomServiceDep, current_user: CurrentUserRoomsDeleteDep
) -> Optional[RoomPublic]:
    return await room_service.end_room(room_id, current_user.id)
