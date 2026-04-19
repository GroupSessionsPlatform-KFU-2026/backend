from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.dependencies.security import get_current_user
from src.app.dependencies.services import RoomServiceDep
from src.app.models.room import RoomCreate, RoomPublic, RoomUpdate
from src.app.models.user import User as UserModel
from src.app.schemas.room_filters import RoomFilters
from src.app.schemas.room_request import JoinRoomRequest

router = APIRouter(
    prefix='/rooms',
    tags=['rooms'],
)

RoomWriteUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['rooms:write']),
]

RoomDeleteUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['rooms:delete']),
]


@router.get('/', dependencies=[Security(get_current_user, scopes=['rooms:read'])])
async def get_rooms(
    filters: Annotated[RoomFilters, Query()],
    room_service: RoomServiceDep,
) -> Sequence[RoomPublic]:
    return await room_service.get_rooms(filters)


@router.post('/')
async def create_room(
    room_create: RoomCreate,
    room_service: RoomServiceDep,
    current_user: RoomWriteUserDep,
) -> RoomPublic:
    return await room_service.create_room(room_create, current_user.id)


@router.post('/join')
async def join_room(
    payload: JoinRoomRequest,
    room_service: RoomServiceDep,
    current_user: RoomWriteUserDep,
):
    return await room_service.join_room(payload, current_user.id)


@router.put('/{room_id}')
async def update_room(
    room_update: RoomUpdate,
    room_id: UUID,
    room_service: RoomServiceDep,
    current_user: RoomWriteUserDep,
) -> Optional[RoomPublic]:
    return await room_service.update_room(room_update, room_id, current_user.id)


@router.delete('/{room_id}')
async def end_room(
    room_id: UUID,
    room_service: RoomServiceDep,
    current_user: RoomDeleteUserDep,
) -> Optional[RoomPublic]:
    return await room_service.end_room(room_id, current_user.id)
