from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, Query

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


async def require_participants_write_access(
    room_id: UUID,
    room_access: RoomAccessServiceDep,
    current_user: CurrentUserParticipantsWriteDep,
) -> None:
    await room_access.ensure_can_moderate(room_id, current_user.id)


async def require_participants_delete_access(
    room_id: UUID,
    room_access: RoomAccessServiceDep,
    current_user: CurrentUserParticipantsDeleteDep,
) -> None:
    await room_access.ensure_can_moderate(room_id, current_user.id)


@router.get('/')
async def get_room_participants(
    room_id: UUID,
    filters: Annotated[RoomParticipantFilters, Query()],
    participant_service: RoomParticipantServiceDep,
    _current_user: CurrentUserParticipantsReadDep,
) -> Sequence[RoomParticipantPublic]:
    return await participant_service.get_participants(room_id, filters)


@router.patch(
    '/{user_id}',
    dependencies=[Depends(require_participants_write_access)],
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
    dependencies=[Depends(require_participants_delete_access)],
)
async def remove_participant(
    room_id: UUID,
    user_id: UUID,
    participant_service: RoomParticipantServiceDep,
) -> Optional[RoomParticipantPublic]:
    return await participant_service.remove_participant(room_id, user_id)
