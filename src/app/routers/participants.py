from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.core.responses import auth_responses, detail_responses
from src.app.dependencies.room_access import require_room_moderation_access
from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import RoomParticipantServiceDep
from src.app.models.room_participant import RoomParticipantPublic, RoomParticipantUpdate
from src.app.schemas.pagination import PaginatedResponse, build_paginated_response
from src.app.schemas.room_participant_filters import RoomParticipantFilters
from src.app.utils.errors import NotFoundError

router = APIRouter(
    prefix='/rooms/{room_id}/participants',
    tags=['participants'],
)


@router.get(
    '/',
    dependencies=[Security(require_scoped_user, scopes=['participants:read'])],
    responses=auth_responses,
)
async def get_room_participants(
    room_id: UUID,
    filters: Annotated[RoomParticipantFilters, Query()],
    participant_service: RoomParticipantServiceDep,
) -> PaginatedResponse[RoomParticipantPublic]:
    participants = await participant_service.get_participants(room_id, filters)
    total = await participant_service.count_participants(room_id, filters)

    return build_paginated_response(
        items=list(participants),
        total=total,
        offset=filters.offset,
        limit=filters.limit,
    )


@router.patch(
    '/{user_id}',
    dependencies=[
        Security(
            require_room_moderation_access,
            scopes=['participants:write'],
        )
    ],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def update_participant(
    room_id: UUID,
    user_id: UUID,
    participant_update: RoomParticipantUpdate,
    participant_service: RoomParticipantServiceDep,
) -> RoomParticipantPublic:
    participant = await participant_service.update_participant(
        room_id,
        user_id,
        participant_update,
    )

    if participant is None:
        raise NotFoundError

    return participant


@router.delete(
    '/{user_id}',
    dependencies=[
        Security(
            require_room_moderation_access,
            scopes=['participants:delete'],
        )
    ],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def remove_participant(
    room_id: UUID,
    user_id: UUID,
    participant_service: RoomParticipantServiceDep,
) -> RoomParticipantPublic:
    participant = await participant_service.remove_participant(room_id, user_id)

    if participant is None:
        raise NotFoundError

    return participant