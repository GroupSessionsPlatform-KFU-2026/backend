from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query

from fastapi import Security
from src.app.dependencies.security import get_current_user
from src.app.models.user import User
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
    room_service: RoomServiceDep,
    filters: Annotated[RoomFilters, Query()],
    current_user: User = Security(get_current_user, scopes=['rooms:read']),
) -> Sequence[RoomPublic]:
    return await room_service.get_rooms(filters)


@router.post('/')
async def create_room(
    room_create: RoomCreate,
    room_service: RoomServiceDep,
    current_user: User = Security(get_current_user, scopes=['rooms:write']),
) -> RoomPublic:
    return await room_service.create_room(room_create)


@router.post('/join')
async def join_room(
    payload: JoinRoomRequest,
    room_service: RoomServiceDep,
    current_user: User = Security(get_current_user, scopes=['rooms:write']),
):
    return await room_service.join_room(payload)


@router.get('/{room_id}')
async def get_room(
    room_service: RoomServiceDep,
    room_id: UUID,
    current_user: User = Security(get_current_user, scopes=['rooms:read']),
) -> Optional[RoomPublic]:
    return await room_service.get_room(room_id)


@router.put('/{room_id}')
async def update_room(
    room_service: RoomServiceDep,
    room_update: RoomUpdate,
    room_id: UUID,
    current_user: User = Security(get_current_user, scopes=['rooms:write']),
) -> Optional[RoomPublic]:
    return await room_service.update_room(room_update, room_id)


@router.delete('/{room_id}')
async def end_room(
    room_service: RoomServiceDep,
    room_id: UUID,
    current_user: User = Security(get_current_user, scopes=['rooms:write']),
) -> Optional[RoomPublic]:
    return await room_service.end_room(room_id)
