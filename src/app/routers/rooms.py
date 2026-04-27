from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.core.responses import auth_responses, conflict_responses, detail_responses
from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import RoomServiceDep
from src.app.models.room import RoomCreate, RoomPublic, RoomUpdate
from src.app.models.room_participant import RoomParticipantPublic
from src.app.models.user import User as UserModel
from src.app.schemas.pagination import PaginatedResponse, build_paginated_response
from src.app.schemas.room_filters import RoomFilters
from src.app.schemas.room_request import JoinRoomRequest
from src.app.utils.errors import NotFoundError

router = APIRouter(
    prefix='/rooms',
    tags=['rooms'],
)


@router.get(
    '/',
    dependencies=[Security(require_scoped_user, scopes=['rooms:read'])],
    responses=auth_responses,
)
async def get_rooms(
    filters: Annotated[RoomFilters, Query()],
    room_service: RoomServiceDep,
) -> PaginatedResponse[RoomPublic]:
    rooms = await room_service.get_rooms(filters)
    total = await room_service.count_rooms(filters)

    return build_paginated_response(
        items=list(rooms),
        total=total,
        offset=filters.offset,
        limit=filters.limit,
    )


@router.post(
    '/',
    responses=auth_responses,
)
async def create_room(
    room_create: RoomCreate,
    room_service: RoomServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['rooms:write']),
    ],
) -> RoomPublic:
    return await room_service.create_room(room_create, current_user.id)


@router.post(
    '/join',
    responses={
        **auth_responses,
        **detail_responses,
        **conflict_responses,
    },
)
async def join_room(
    payload: JoinRoomRequest,
    room_service: RoomServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['rooms:write']),
    ],
) -> RoomParticipantPublic:
    participant = await room_service.join_room(payload, current_user.id)

    if participant is None:
        raise NotFoundError

    return participant


@router.put(
    '/{room_id}',
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def update_room(
    room_update: RoomUpdate,
    room_id: UUID,
    room_service: RoomServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['rooms:write']),
    ],
) -> RoomPublic:
    room = await room_service.update_room(room_update, room_id, current_user.id)

    if room is None:
        raise NotFoundError

    return room


@router.delete(
    '/{room_id}',
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def end_room(
    room_id: UUID,
    room_service: RoomServiceDep,
    current_user: Annotated[
        UserModel,
        Security(require_scoped_user, scopes=['rooms:delete']),
    ],
) -> RoomPublic:
    room = await room_service.end_room(room_id, current_user.id)

    if room is None:
        raise NotFoundError

    return room
