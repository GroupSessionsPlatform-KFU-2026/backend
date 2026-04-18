from dataclasses import dataclass
from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Security

from src.app.dependencies.security import get_current_user
from src.app.dependencies.services import (
    RoomAccessServiceDep,
    RoomParticipantServiceDep,
)
from src.app.models.room_participant import RoomParticipantPublic, RoomParticipantUpdate
from src.app.models.user import User as UserModel
from src.app.schemas.room_participant_filters import RoomParticipantFilters
from src.app.services.room_access import RoomAccessService
from src.app.services.room_participants import RoomParticipantService

router = APIRouter(
    prefix='/rooms/{room_id}/participants',
    tags=['participants'],
)


CurrentParticipantWriteUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['participants:write']),
]

CurrentParticipantDeleteUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['participants:delete']),
]


@dataclass(slots=True)
class ParticipantMutationDeps:
    participant_service: RoomParticipantService
    room_access: RoomAccessService


def get_participant_mutation_deps(
    participant_service: RoomParticipantServiceDep,
    room_access: RoomAccessServiceDep,
) -> ParticipantMutationDeps:
    return ParticipantMutationDeps(
        participant_service=participant_service,
        room_access=room_access,
    )


ParticipantMutationDepsDep = Annotated[
    ParticipantMutationDeps,
    Depends(get_participant_mutation_deps),
]


@router.get(
    '/',
    dependencies=[Security(get_current_user, scopes=['participants:read'])],
)
async def get_room_participants(
    room_id: UUID,
    filters: Annotated[RoomParticipantFilters, Query()],
    participant_service: RoomParticipantServiceDep,
) -> Sequence[RoomParticipantPublic]:
    return await participant_service.get_participants(room_id, filters)


@router.patch('/{user_id}')
async def update_participant(
    room_id: UUID,
    user_id: UUID,
    participant_update: RoomParticipantUpdate,
    deps: ParticipantMutationDepsDep,
    current_user: CurrentParticipantWriteUserDep,
) -> Optional[RoomParticipantPublic]:
    await deps.room_access.ensure_can_moderate(room_id, current_user.id)
    return await deps.participant_service.update_participant(
        room_id,
        user_id,
        participant_update,
    )


@router.delete('/{user_id}')
async def remove_participant(
    room_id: UUID,
    user_id: UUID,
    deps: ParticipantMutationDepsDep,
    current_user: CurrentParticipantDeleteUserDep,
) -> Optional[RoomParticipantPublic]:
    await deps.room_access.ensure_can_moderate(room_id, current_user.id)
    return await deps.participant_service.remove_participant(room_id, user_id)
