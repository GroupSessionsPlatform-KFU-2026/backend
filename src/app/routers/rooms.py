from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.app.dependencies.services import RoomServiceDep
from src.app.models.room import RoomCreate, RoomPublic, RoomUpdate
from src.app.schemas.room_filters import RoomFilters


# This class DTO where I should move? schemes/models?
class JoinRoomRequest(BaseModel):
    room_code: str
    user_id: UUID


router = APIRouter(
    prefix='/rooms',
    tags=['rooms'],
)


@router.get('/')
async def get_rooms(
    room_service: RoomServiceDep,
    filters: Annotated[RoomFilters, Query()],
) -> Sequence[RoomPublic]:
    return await room_service.get_rooms(filters)


@router.post('/')
async def create_room(
    room_create: RoomCreate,
    room_service: RoomServiceDep,
) -> RoomPublic:
    return await room_service.create_room(room_create)


@router.post('/join')
async def join_room(
    payload: JoinRoomRequest,
    room_service: RoomServiceDep,
):
    return await room_service.join_room(payload)


@router.get('/{room_id}')
async def get_room(
    room_service: RoomServiceDep,
    room_id: UUID,
) -> Optional[RoomPublic]:
    return await room_service.get_room(room_id)


@router.put('/{room_id}')
async def update_room(
    room_service: RoomServiceDep,
    room_update: RoomUpdate,
    room_id: UUID,
) -> Optional[RoomPublic]:
    return await room_service.update_room(room_update, room_id)


@router.delete('/{room_id}')
async def end_room(
    room_service: RoomServiceDep,
    room_id: UUID,
) -> Optional[RoomPublic]:
    return await room_service.end_room(room_id)
