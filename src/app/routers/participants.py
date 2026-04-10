from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query, Depends

from fastapi import Security
from src.app.dependencies.security import get_current_user
from src.app.models.user import User
from src.app.services.room_participants import RoomParticipantService
from src.app.models.room_participant import RoomParticipantPublic, RoomParticipantUpdate
from src.app.schemas.room_participant_filters import RoomParticipantFilters

router = APIRouter(
    prefix='/rooms/{room_id}/participants',
    tags=['participants'],
)


@router.get('/')
async def get_room_participants(
    room_id: UUID,
    filters: Annotated[RoomParticipantFilters, Query()],
    participant_service: RoomParticipantService = Depends(),
    current_user: User = Security(get_current_user, scopes=['participants:read']),
) -> Sequence[RoomParticipantPublic]:
    return await participant_service.get_participants(room_id, filters)


@router.patch('/{user_id}')
async def update_participant(
    room_id: UUID,
    user_id: UUID,
    participant_update: RoomParticipantUpdate,
    participant_service: RoomParticipantService = Depends(),
    current_user: User = Security(get_current_user, scopes=['participants:write']),
) -> Optional[RoomParticipantPublic]:
    # TODO: validate room moderation permissions after OAuth2 is implemented.
    return await participant_service.update_participant(
        room_id,
        user_id,
        participant_update,
    )


@router.delete('/{user_id}')
async def remove_participant(
    room_id: UUID,
    user_id: UUID,
    participant_service: RoomParticipantService = Depends(),
    current_user: User = Security(get_current_user, scopes=['participants:delete']),
) -> Optional[RoomParticipantPublic]:
    # TODO: validate room moderation permissions after OAuth2 is implemented.
    return await participant_service.remove_participant(room_id, user_id)
