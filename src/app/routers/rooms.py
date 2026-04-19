from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import RoomServiceDep
from src.app.models.room import RoomCreate, RoomPublic, RoomUpdate
from src.app.models.user import User as UserModel
from src.app.schemas.room_filters import RoomFilters
from src.app.schemas.room_request import JoinRoomRequest

router = APIRouter(
    prefix='/rooms',
    tags=['rooms'],
)


@router.get('/', dependencies=[Security(require_scoped_user, scopes=['rooms:read'])])
async def get_rooms(
    filters: Annotated[RoomFilters, Query()],
    room_service: RoomServiceDep,
) -> Sequence[RoomPublic]:
    return await room_service.get_rooms(filters)


@router.post('/')
async def create_room(
    room_create: RoomCreate,
    room_service: RoomServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['rooms:write']),
    ],
) -> RoomPublic:
    return await room_service.create_room(room_create, current_user.id)


@router.post('/join')
async def join_room(
    payload: JoinRoomRequest,
    room_service: RoomServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['rooms:write']),
    ],
):
    return await room_service.join_room(payload, current_user.id)


@router.put('/{room_id}')
async def update_room(
    room_update: RoomUpdate,
    room_id: UUID,
    room_service: RoomServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['rooms:write']),
    ],
) -> Optional[RoomPublic]:
    return await room_service.update_room(room_update, room_id, current_user.id)


@router.delete('/{room_id}')
async def end_room(
    room_id: UUID,
    room_service: RoomServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['rooms:delete']),
    ],
) -> Optional[RoomPublic]:
    return await room_service.end_room(room_id, current_user.id)
