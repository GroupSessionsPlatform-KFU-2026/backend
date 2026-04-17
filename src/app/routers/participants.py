from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query

from src.app.dependencies.security import (
    CurrentUserParticipantsDeleteDep,
    CurrentUserParticipantsReadDep,
    CurrentUserParticipantsWriteDep,
)
from src.app.dependencies.services import (
    RoomAccessServiceDep,
    RoomParticipantServiceDep,
)
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
    participant_service: RoomParticipantServiceDep,
    _current_user: CurrentUserParticipantsReadDep,
) -> Sequence[RoomParticipantPublic]:
    return await participant_service.get_participants(room_id, filters)


@router.patch('/{user_id}')
async def update_participant(  # noqa: PLR0913
    room_id: UUID,
    user_id: UUID,
    participant_update: RoomParticipantUpdate,
    participant_service: RoomParticipantServiceDep,
    room_access: RoomAccessServiceDep,
    current_user: CurrentUserParticipantsWriteDep,
) -> Optional[RoomParticipantPublic]:
    await room_access.ensure_can_moderate(room_id, current_user.id)
    return await participant_service.update_participant(
        room_id,
        user_id,
        participant_update,
    )


@router.delete('/{user_id}')
async def remove_participant(
    room_id: UUID,
    user_id: UUID,
    participant_service: RoomParticipantServiceDep,
    room_access: RoomAccessServiceDep,
    current_user: CurrentUserParticipantsDeleteDep,
) -> Optional[RoomParticipantPublic]:
    await room_access.ensure_can_moderate(room_id, current_user.id)
    return await participant_service.remove_participant(room_id, user_id)