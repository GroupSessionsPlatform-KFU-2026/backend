from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query

from src.app.dependencies.services import RoomServiceDep
from src.app.models import BaseModel
from src.app.models.room import RoomCreate, RoomPublic, RoomUpdate
from src.app.models.room_participant import RoomParticipantPublic
from src.app.schemas.room_filters import RoomFilters


class JoinRoomRequest(BaseModel):
    room_code: str


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
    # temporal: luego creator_id viene del auth
    return await room_service.create_room(1, room_create)


@router.post('/join')
async def join_room(
    payload: JoinRoomRequest,
    room_service: RoomServiceDep,
) -> Optional[RoomParticipantPublic]:
    return await room_service.join_room(payload.room_code, 1)


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
