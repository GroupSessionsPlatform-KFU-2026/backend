from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.dependencies.room_access import require_room_moderation_access
from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import RoomParticipantServiceDep
from src.app.models.room_participant import RoomParticipantPublic, RoomParticipantUpdate
from src.app.schemas.room_participant_filters import RoomParticipantFilters

router = APIRouter(
    prefix='/rooms/{room_id}/participants',
    tags=['participants'],
)


@router.get(
    '/',
    dependencies=[Security(require_scoped_user, scopes=['participants:read'])],
)
async def get_room_participants(
    room_id: UUID,
    filters: Annotated[RoomParticipantFilters, Query()],
    participant_service: RoomParticipantServiceDep,
) -> Sequence[RoomParticipantPublic]:
    return await participant_service.get_participants(room_id, filters)


@router.patch(
    '/{user_id}',
    dependencies=[
        Security(
            require_room_moderation_access,
            scopes=['participants:write'],
        )
    ],
)
async def update_participant(
    room_id: UUID,
    user_id: UUID,
    participant_update: RoomParticipantUpdate,
    participant_service: RoomParticipantServiceDep,
) -> Optional[RoomParticipantPublic]:
    return await participant_service.update_participant(
        room_id,
        user_id,
        participant_update,
    )


@router.delete(
    '/{user_id}',
    dependencies=[
        Security(
            require_room_moderation_access,
            scopes=['participants:delete'],
        )
    ],
)
async def remove_participant(
    room_id: UUID,
    user_id: UUID,
    participant_service: RoomParticipantServiceDep,
) -> Optional[RoomParticipantPublic]:
    return await participant_service.remove_participant(room_id, user_id)
